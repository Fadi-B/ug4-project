#pragma once

#include <Eigen/Dense>
#include "assert.h"
#include <stdio.h>

#include <fdeep/fdeep.hpp>


class KF
{

public:

    static const int iBias = 0;
    static const int iBand = 1;
    static const int iRTTG = 2;
    static const int iQueueDelay = 3;
    static const int iInterArrival = 4;

    static const int HISTORY_SIZE = 3;

    /* State will be [bias, Throughput, RTT Grad, Queue Delay, Inter Arrival]
     *
     * However, we will only have 1 bias through all historic states, which is why we encode the state size as 4
     *
     * The ignore constants will take binary values to indicate whether a specific feature should be ignored or not.
     * Any other values than binary will break the program. They should be one-hot encoded.
     */

    static const int INTER_ARRIVAL_IGNORE = 0;
    static const int RTT_GRAD_IGNORE = 0;
    static const int QUEUE_DELAY_IGNORE = 0;

    static const int STATE_SIZE = 4 - INTER_ARRIVAL_IGNORE - RTT_GRAD_IGNORE - QUEUE_DELAY_IGNORE;

    /* Note: The +1 at the end is to make sure we include an additional space for the bias
     *
     */
    static const int DIM = HISTORY_SIZE * STATE_SIZE + 1;

    typedef Eigen::Matrix<double, DIM, 1> Vector;
    typedef Eigen::Matrix<double, DIM, DIM> Matrix;

    //Will determine whether to do non-linear (less interpretable forecasting)
    //Requires that the model is specified as a fdeep json model in the current working directory
    static const uint8_t MODE_NON_LINEAR = 0;

    KF(double initBandwidth, double initRTTGrad, double initQueueDelay, double initInterArrival)
    {

        /* State Initialization */

        std::vector<double> init(STATE_SIZE, 0);

        if (RTT_GRAD_IGNORE)
        {

          init = {initBandwidth, initQueueDelay, initInterArrival};

        }
        else if (QUEUE_DELAY_IGNORE)
        {

          init = {initBandwidth, initRTTGrad, initInterArrival};

        }
        else if (INTER_ARRIVAL_IGNORE)
        {

          init = {initBandwidth, initRTTGrad, initQueueDelay};

        }
        else
        {

          init = {initBandwidth, initRTTGrad, initQueueDelay, initInterArrival};

        }

	// Adding Bias
        _mean(0, 0) = 1;

        for (int i = 0; i < DIM - 1; i++)
        {

	  //For now initialize all other historic data as 0
	  if (i < STATE_SIZE)
          {

            _mean(i+1, 0) = init[i];

          }

          else
          {

           _mean(i+1, 0) = 0;

          }

        }

        _cov.setIdentity();

        /* Transition Matrix Initialization */
        F = Matrix::Identity(DIM, DIM);

        /* Noiseless connection between measurement and state initialization */
        H = Matrix::Identity(DIM, DIM); // For now we assume a unity connection

        _kap = 3 - DIM; //standard to use this value
        alpha_0 = _kap / (_kap + DIM);
        alpha = 1 / (2*(_kap + DIM));


    }


    Vector system_transformation(Vector sig_point, int tick)
    {

      //Will define our function here - no restrictions on it

      Vector pred = sig_point;

      if (MODE_NON_LINEAR)
      {

	//For now gives <rttgrad, queue_delay, inter arrival time>
	std::vector<float> features = eigen_data_to_vector(sig_point);
//        bool is_zero = std::all_of(features.begin(), features.end(), [](int i) { return i==0; });
        bool is_zero = false;
	double prediction = sig_point(iBand, 0);

        if (!is_zero)
        {

          //Note: Model does not include a bias term at the moment
          const auto result = _model.predict(
          { fdeep::tensor( fdeep::tensor_shape(static_cast<std::size_t>(1), static_cast<std::size_t>(3)) , features) });

          const std::vector<float> to_vec = result[0].to_vector();

//          fprintf(stderr, "TICK: %d \n", tick);

//          std::cerr << fdeep::show_tensors(result) << std::endl;
          //fprintf(stderr, "Size: %d \n", to_vec.size());
//          fprintf(stderr, "Change: %f \n", to_vec[tick]);

          //Add the change to our current mean value
          prediction = prediction + to_vec[tick];

        }

        pred[iBand] = std::max(prediction, (double)0);
        fprintf(stderr, "Pred: %f \n", prediction);

      }
      else
      {

        pred = F * sig_point;

      }

      return pred;

    }

    //For now we have unity transformation between true state and measurement state
    Vector observation_transformation(Vector sig_point)
    {

      return sig_point;

    }

    Eigen::Matrix<double, 2*DIM + 1, DIM> compute_sigma_points()
    {

      Eigen::LLT<Matrix> LL(_cov); //Make sure we get the stds

      Matrix L = LL.matrixL();


      //Will hold all our signma points in the rows
      Eigen::Matrix<double, 2*DIM + 1, DIM> sigma_points;

      sigma_points.row(0) = _mean.transpose();

      for (int i = 0; i < DIM; i++)
      {

        Vector translation = (std::sqrt(_kap + DIM))*(L.col(i));

        Vector sig_right = _mean + translation;
        Vector sig_left = _mean - translation;

        //sigma_points matrix will hold two conjugate points in consecutive positions
        sigma_points.row(2*i + 1) = sig_right.transpose();
        sigma_points.row(2*i + 2) = sig_left.transpose();

      }

      return sigma_points;

    }

    Vector compute_mean(Eigen::Matrix<double, 2*DIM + 1, DIM> sigma_points_transformed)
    {


      /* Computing the new mean and covariance */

      Vector new_mean = alpha_0 * sigma_points_transformed.row(0).transpose();

      for (int i = 1; i < 2*DIM + 1; i++)
      {

        new_mean = new_mean + alpha * sigma_points_transformed.row(0).transpose();

      }

      return new_mean;

    }

    Matrix compute_cov(Eigen::Matrix<double, 2*DIM + 1, DIM> sigma_points_transformed, Vector new_mean)
    {
      
      Vector sig_0 = sigma_points_transformed.row(0).transpose();
      Matrix new_cov = alpha_0 * ((sig_0 - new_mean)*(sig_0 - new_mean).transpose());

      for (int i = 1; i < 2*DIM + 1; i++)
      {
        
        Vector sig = sigma_points_transformed.row(i).transpose();
        new_cov = new_cov + alpha * ((sig - new_mean)*(sig - new_mean).transpose());

      }

      return new_cov;

    }

    void predict(Matrix Q, int tick)
    {

    /* Computing the Sigma Points */
      Eigen::Matrix<double, 2*DIM + 1, DIM> sigma_points = compute_sigma_points();


      Eigen::Matrix<double, 2*DIM + 1, DIM> sigma_points_transformed;

      /* Transforming all sigma points */
      for (int i = 0; i < 2*DIM + 1; i++)
      {

        Vector transformed = system_transformation(sigma_points.row(i).transpose(), tick);

        sigma_points_transformed.row(i) = transformed.transpose();

      }


      /* Computing the new mean and covariance */

      Vector new_mean = compute_mean(sigma_points_transformed);

      fprintf(stderr, "Mean: %f \n", new_mean(iBand, 0));

      Matrix new_cov = compute_cov(sigma_points_transformed, new_mean);


      // Max function does not seem to work so will be doing it manually
      double throughput = new_mean[iBand];

      if (throughput <= 0)
      {
	      new_mean[iBand] = 0;
      }

      _cov = new_cov + Q; //Add additive uncertainty noise
      _mean = new_mean;

    }


    void update(Vector measurement, Matrix measurementVar)
    {

      	Eigen::IOFormat CleanFmt(4, 0, ", ", "\n", "[", "]");


      //Compute the new updates sigma points as mean and covariance have changed
      Eigen::Matrix<double, 2*DIM + 1, DIM> sigma_points = compute_sigma_points();

      Eigen::Matrix<double, 2*DIM + 1, DIM> transformed;

      /* Transforming all sigma points */
      for (int i = 0; i < 2*DIM + 1; i++)
      {

        //Maps them to the measurement space
        Vector tran = observation_transformation(sigma_points.row(i).transpose());

        transformed.row(i) = tran.transpose();

      }

      Vector z_mean = compute_mean(transformed);
      Matrix z_cov = compute_cov(transformed, z_mean) + measurementVar; //Make sure to add additive noise

      /* Computing cross-covariance matrix */

      Matrix cross_cov = alpha_0 * ((sigma_points.row(0).transpose() - _mean)*(transformed.row(0).transpose() - z_mean).transpose());

      for (int i = 1; i < 2*DIM + 1; i++)
      {

        Vector sig = sigma_points.row(i).transpose();
        Vector meas = transformed.row(i).transpose();

        cross_cov = cross_cov + alpha * ((sig - _mean)*(meas - z_mean).transpose());

      }

       /* Computing Kalman Gain */

      Matrix K = kalman_gain(z_cov, cross_cov); //fix this - will prob throw error

      Vector new_mean = _mean + K * (measurement - z_mean);
      Matrix new_cov = _cov - K * z_cov * K.transpose();


      new_mean[iBias] = 1; // Bias

      // Max function does not seem to work so will be doing it manually
      double throughput = new_mean[iBand];

      if (throughput < 0)
      {
         new_mean[iBand] = 0;
      }

      if (RTT_GRAD_IGNORE || QUEUE_DELAY_IGNORE || INTER_ARRIVAL_IGNORE)
      {

        //Will put things in correct entry
        new_mean[2] = measurement[2];
        new_mean[3] = measurement[3];

      }
      else
      {

       new_mean[iRTTG] = measurement[iRTTG]; 		  	// RTT Gradient
       new_mean[iQueueDelay] = measurement[iQueueDelay];	// Queuing Delay
       new_mean[iInterArrival] = measurement[iInterArrival];   // Inter arrival time

      }

      _cov = new_cov;
      _mean = new_mean;

	//std::cerr << "\n New Mean \n" << K.format(CleanFmt);

        return;

    }

    Vector innovation(Vector measurement)
    {
        Vector innov = measurement - H * _mean;

	Eigen::IOFormat CleanFmt(4, 0, ", ", "\n", "[", "]");
        //std::string sep = "\n----------------------------------------\n";

        //std::cerr << "\n Innov \n" << innov.format(CleanFmt);
        //std::cerr << "\n Meas. \n" << measurement.format(CleanFmt);
	//std::cerr << "\n Mean \n" << _mean.format(CleanFmt);

        return innov;
    }

    Matrix innovation_cov(Matrix R)
    {
        Matrix S = H * _cov * H.transpose() + R;

        return S;
    }

    Matrix kalman_gain(Matrix z_cov, Matrix cross_cov)
    {

        //printf("SIZE: %d\n", (_cov * H.transpose()).size());

	/* We will compute the kalman gain without explicitly
	 * inverting the S matrix as this can produce issues if S is not fully invertible
	 * due to numerical precision etc.
	 *
	 * Will solve for x in S.T*x = H*P.T as this will give K.T
	 *
	 * From which K can be easily obtained by transposing the result
	 *
	 */
	Matrix A = z_cov.transpose();

	Matrix x = A.colPivHouseholderQr().solve(cross_cov.transpose()); // computes A^-1 * b
	Matrix K_solv = x.transpose();

        //Matrix K_solv = _cov * H.transpose() * S.inverse();

	Eigen::IOFormat CleanFmt(4, 0, ", ", "\n", "[", "]");
        //std::string sep = "\n----------------------------------------\n";

        //std::cerr << "\n S \n" << S.format(CleanFmt);
	//std::cerr << "\n S Inv \n" << S.inverse().format(CleanFmt);
        //std::cerr << "\n Cov. \n" << _cov.format(CleanFmt);
        //std::cerr << "\n K \n" << K.format(CleanFmt);
	//std::cerr << "\n K Solv \n" << K_solv.format(CleanFmt);

        return K_solv;
    }

    void setF(Matrix newF)
    {

        F = newF;

    }

    void setCov(Matrix newCov)
    {
        _cov = newCov;
    }

    void reset()
    {
        //TO DO
        return;

    }


    /**
     * @brief Utility function for converting between eigen matrices and tensors
     * 
     * @return 
     */

    std::vector<float> eigen_data_to_vector(Vector state)
    {

      Eigen::IOFormat CleanFmt(4, 0, ", ", "\n", "[", "]");
       //std::cerr << "\n state \n" << state.format(CleanFmt);

      //Size 3
      std::vector<float> data;
      data.reserve(DIM - iRTTG);


      //We just want to get prediction data (RTTG - IRT)
      for (int i = iRTTG; i < DIM; i++)
      {

        double elem = state[i];
        data.push_back(elem);
        //fprintf(stderr, "Adding: %f \n", data[i - iRTTG]);

      }

      return data;

    }



    Matrix cov()
    {
        return _cov;
    }

    Vector mean()
    {
        return _mean;
    }

    double bandwidth()
    {
        return _mean(iBand);
    }

    double RTTGrad()
    {
        return _mean(iRTTG);
    }

    double delay()
    {
        return _mean(iQueueDelay);
    }

private:

    /* State Space Representation */
    Vector _mean;
    Matrix _cov;

    /* Transition Matrix */
    Matrix F;

    /* Noiseless connection between measurement and state */
    Matrix H;

    double _kap;
    double alpha_0;
    double alpha;

    //Load in the non-linear model
    const fdeep::model _model = fdeep::load_model("fdeep_model.json");

/* Creating the Gaussian Noise generator */
    //NoiseGenerator * gen = new NoiseGenerator(0, 0, 0.01); //seed, mean, std
    //NoiseGenerator::Generator generator = (*gen).get_generator();

};





