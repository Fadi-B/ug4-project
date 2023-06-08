#pragma once

#include <Eigen/Dense>
#include <stdio.h>
#include "assert.h"
#include "kalman_filter.hh"

#include "packet_collector.hh"

#include <fdeep/fdeep.hpp>

#include <list>

class KFForecaster
{

public:


    //using KF::DIM;
    //using KF::Matrix;

    static const uint16_t bits = PacketCollector::MSS * PacketCollector::BYTE_SIZE;
    static const uint16_t ms_per_sec = 60; /* We should be careful with this one as we are forecasting 20ms into the future*/
    static const uint8_t iModel = 1;

    static const uint16_t NUM_TICKS = 3;


    KFForecaster(double initBandwidth, double initRTTGrad, double initQueueDelay, double initInterArrival)
    :state(initBandwidth, initRTTGrad, initQueueDelay, initInterArrival)
    {

          /* Initialize the transition model */
       	  initForecastModel();

          KF::Matrix F = KF::Matrix::Identity(KF::DIM, KF::DIM);
//        F.row(iModel) = forecastModel.transpose(); //Slightly unsure if this would work so should confirm

          /* Note: Uncertainty Matrix is initialized to identity in KF class - No need to set it */

          state.setF(F);

          /* Initialize the noise covariances*/
          initQ();
          initR();

          _start_time_point = chrono::high_resolution_clock::now();

          for (int i = 0; i < NUM_TICKS; i++)
          {

	    prev_forecast[i] = initBandwidth;
            Q_values(0, i) = 0.0;

          }

          correct_Q_count = 0;

    }

    /* For debugging */
    void showdata (double *data,  int n) {
  	int i; 

	if (1) {
    	fprintf (stderr, "Bytes to be drained");
    	for (i=0; i<n; i++ ){
    	 fprintf (stderr, " %f", data[i]);
    	}
   	 fprintf(stderr, "\n");
  	}
    }

    void forecast(int tick_number)
    {

        //fprintf(stderr, "Tick Nuymber: %d \n", tick_number);

        KF::Matrix F = KF::Matrix::Identity(KF::DIM, KF::DIM);

        double now = CollectorManager::getCurrentTime(_start_time_point);

        for (int i=0; i < tick_number; i++)
        {

//	    fprintf(stderr, "PRE: %f \n", state.mean()(KF::iBand));

           if (now > 3500)
           {

            F.row(iModel) = forecastModel.row(i);
            state.setF(F);

            state.predict(Qs[i], i);

           }
	    //fprintf(stderr, "Adding new: \n");
            //state.predict(Qs[i], i);

            prev_forecast[i] = state.mean()(KF::iBand);

//            state.mean()(KF::iBand) = 3.4;

//            fprintf(stderr, "Post: %f \n", state.mean()(KF::iBand));

            if (i == 0)
            {

                //fprintf(stderr, "Forecast Prediction: %f \n", state.mean()(KF::iBand));

                bytes_to_be_drained[i] = getForecastedBytes(i);

            }
            else
            {

                //double cum_drained = *(bytes_to_be_drained.rbegin()) + getForecastedBytes();

                bytes_to_be_drained[i] = bytes_to_be_drained[i - 1] + getForecastedBytes(i);

            }

        }

       //Will not be changed anymore
       start = true;

      //clearForecast();
      //showdata(bytes_to_be_drained, 8);

    }

    void correctForecast(CollectorManager::Matrix observed)
    {
        double now = CollectorManager::getCurrentTime(_start_time_point);

        if (now > 3500) {


        if (correct_Q_count == NUM_TICKS) {correct_Q_count = 0;}

//        fprintf(stderr, "BW: %f \n", observed.row(0)(0, 0));

        double res = prev_forecast[correct_Q_count] - observed.row(0)(0, 0); //bandwidth at index 0

        Q_values(0, correct_Q_count) = res*res; //use res as the std

  //      fprintf(stderr, "res*res: %f\n", Q_values(0, correct_Q_count));

	Qs[correct_Q_count](KF::iBand, KF::iBand) = Q_values(0, correct_Q_count);

    //    fprintf(stderr, "Inside Qs i=%d: %f \n", correct_Q_count, Qs[correct_Q_count](KF::iBand, KF::iBand));

        correct_Q_count = correct_Q_count + 1;

        }

        //fprintf(stderr, "Correct:\n");

        Eigen::IOFormat CleanFmt(4, 0, ", ", "\n", "[", "]");

        Eigen::Matrix<double, KF::DIM, 1> obs; //= observed.row(0).transpose();

//        std::cerr << "\n Measurement \n" << observed.format(CleanFmt) << "\n";

      	for (int i = 0; i < KF::HISTORY_SIZE; i++)
        {
	  //108
          Eigen::Matrix<double, 1, KF::STATE_SIZE> data = observed.row(i);


          for (int j = 0; j < KF::STATE_SIZE; j++)
          {

	    // Note: The +1 is to make sure we do not override bias
	    obs(i*KF::STATE_SIZE + j + 1, 0) = data(0, j);

          }

        }

       // Adding the bias
       obs(0,0) = 1;

  //     std::cerr << "\n OBS-Post \n" << obs.format(CleanFmt) << "\n";

        double b = ((ms_per_sec * 1000) * obs(KF::iBand, 0))/bits;

//       fprintf(stderr, "Correct Obs: %f \n", b);
//        fprintf(stderr, "Current Mean: %f \n", state.mean()(KF::iBand));
//	fprintf(stderr, "Correcting \n");
        state.update(obs, R);

    }

    double getForecastedBytes(int i)
    {

	double uncertainty = Qs[i](KF::iBand, KF::iBand);
	double stddev = std::sqrt(uncertainty);

	//fprintf(stderr, "Stddev: %f \n", stddev);

        /* Stored in Mbits/s */

        double now = CollectorManager::getCurrentTime(_start_time_point);

        double factor = 0;

        if (now > 3500)
        {

          factor = 0*stddev;

        }


        double rate = state.mean()(KF::iBand) - factor;

//        fprintf(stderr, "RATE: %f \n", rate);

        double bytes =  std::max(((ms_per_sec * 1000) * rate) / bits, 0.25);

        //if (bytes == 0.1) {/*start_up = 10 + now;*/ fprintf(stderr, "N\n");}

        fprintf(stderr, "Bytes: %f \n", bytes);

        return bytes;

    }

    double * getBytesToBeDrained()
    {
        return bytes_to_be_drained;
    }

    void clearForecast()
    {

        for (int i = 0; i < NUM_TICKS; i++)

	    {

	        bytes_to_be_drained[i] = 0;

	    }

    }

    KF getState()
    {
	return state;
    }

    void setQ(KF::Matrix newQ)
    {

        Q = newQ;

    }

    void setR(KF::Matrix newR)
    {

        R = newR;

    }

private:

    //To avoid odd behavior during start up
    bool start = false;
    double start_up;

    double prev_forecast[NUM_TICKS];
    int correct_Q_count;

    std::chrono::high_resolution_clock::time_point _start_time_point;

    KF state;


    KF::Matrix Qs[NUM_TICKS];
    /* Noise covariances */
    KF::Matrix Q;   /* System Noise Covariance */
    KF::Matrix R;   /* Observation Noise Covariance */

    /* Forecast Model that we have learnt offline */
    Eigen::Matrix<double, NUM_TICKS, KF::DIM> forecastModel;
    Eigen::Matrix<double, 1, NUM_TICKS> Q_values;

    double bytes_to_be_drained[NUM_TICKS];


    /* Initialization functions */
    void initForecastModel()
    {

        /* Note: It seems that removing terms and relearning a new model based on those performs roughly the same 
         * Most likely because model learn compensates for the previous things - might indicate that they all tell us the same thing?
         */

        double COLUMN = 0; /* Vector will just have 1 column */

        /* Will hold weights corresponding to bias, rtt gradient, queuing delay and inter arrival time */
        //double params[KF::DIM] = {-0.00120897, 1, -0.0000451813877, -0.000013251127, 0.00024678328}; //TMobile UMTS


        //double params[KF::DIM] = {0,1,0,0,0};


        //double params[8][KF::DIM] = {{0.05902253, 1, 0.00023383, -0.0010024 ,  0.00124224},
        //{-0.00639942, 1, 2.15790548e-04, 4.18576614e-05, 1.67243052e-04}, 
        //{0.01497034, 1, -0.00042156, -0.00023359,  0.00010058}, 
        //{0.01890435, 1, 5.79744307e-04, -2.43326647e-04, -6.67425321e-05}, 
        //{-0.03524784, 1, -0.00259395,  0.00034825,  0.00032649}, 
        //{-0.01470577, 1, -2.36631317e-03,  6.08377038e-05,  4.86204102e-04},
        //{0.01216091, 1, 0.00244498, -0.00011558, -0.0001529},
        //{0.01307779, 1, 2.41631104e-03, -1.45166175e-04, -5.37754775e-05}};


	/* ATT-LTE */
//        double params[NUM_TICKS][KF::DIM] = {{0.01801426, 1,-1.06796990e-03, -9.41025575e-05, -3.39285804e-04 },
//        {-0.01826752, 1, 0.00078856, 0.0002721 , 0.00021981},
//        {0.00218566, 1, 1.94470020e-05, -1.23671650e-04,  4.03347048e-05},
//        {7.82062257e-07, 1, -2.11112688e-04,  7.20039455e-06, -1.12194602e-05}};

	/* TMobile-UMTS */
        //double params[NUM_TICKS][KF::DIM] = {{0.00435237, 1, -6.37146134e-05, -1.22553605e-05, -1.81571702e-04 },
        //{0.00594969, 1, 1.85622260e-05, -3.40788008e-07, -3.39877724e-04},
        //{0.00140947, 1, -2.91711709e-05,  2.37781023e-05, -2.40186158e-04},
        //{-0.00994084, 1, -8.18415588e-04,  5.73744062e-05,  9.55001453e-05}};

        /* Verizon-EVDO */
        //double params[NUM_TICKS][KF::DIM] = {{0.03562452, 1,-0.0003659 ,  0.00026451, -0.00089912 },
        //{0.02882335, 1,-9.20557188e-04,  6.42449339e-05, -6.52298600e-04},
        //{-0.0225616, 1, -0.00042147, -0.00014442,  0.00055037},
        //{0.01327253, 1, -8.55697209e-05, -4.18441525e-05, -2.56607457e-04}};


	/* TMobile-LTE */
//        double params[NUM_TICKS][KF::DIM] = {{1.24363828, 1,-0.4977323 , -0.00890786, -0.03032131 },
//        {0.18507001, 1, -0.35585721, -0.00107478, -0.0137142},
//        {-0.85124671, 1, -0.5077448 ,  0.00693351, -0.00761094},
//        {-0.77906561, 1, 0.41034358, 0.00544913, 0.02229775}};

        /* CURRENT */
//        double params[NUM_TICKS][KF::DIM] = {{0, 1, 0 , 0, 0},
//        {0, 1, 0, 0, 0},
//        {0, 1, 0, 0, 0},
//        {0, 1, 0, 0, 0}};


        /* LIN Historic - TMob-UMTS */
        double params[NUM_TICKS][KF::DIM] = {{-0.00417372, 1, 1.38115905e-04, -9.39491044e-06, -3.53076788e-04, 0, 2.09444906e-04,
                  1.11435065e-05, -1.21761322e-03, 0, -9.42874165e-04,  3.87112269e-05,
                  1.48479716e-03},
        {-0.00613785, 1, 2.37968253e-04,  1.75247653e-05, -1.62492346e-03, 0, -9.96440842e-04,
                  4.90448775e-05,  3.38010041e-04, 0, 6.24496833e-04, -3.68413177e-05,
                  1.41929303e-03},
        {-5.62194811e-05, 1, -1.02331970e-03,  5.53887817e-05, -7.58774632e-04, 0, 5.16792747e-04,
                 -2.92201535e-05,  2.39766418e-03, 0, 1.04472089e-04, -2.79035606e-05,
                 -1.62597847e-03}};

        /* Verizon-LTE */
        //double params[NUM_TICKS][KF::DIM] = {{-0.022903, 1, -0.01952263,  0.00012621, -0.0002273 },
        //{-0.04704366, 1, -1.81237028e-02,  2.97592119e-04,  6.82349876e-05},
        //{-0.01526759, 1, 0.01610724, 0.00013797, 0.00012053},
        //{-0.01245914, 1, -5.85720143e-03,  6.73440803e-05,  4.27452228e-05}};

        for (int i = 0; i < NUM_TICKS; i++) 
        {

        for (int j = 0; j < KF::DIM; j++)
        {

            forecastModel(i, j) = params[i][j];

        }

      }

    }

    void initQ()
    {

	Q.setZero();

        /* For now will assume everything else has noise 0 */
        Q(KF::iBand, KF::iBand) = 0;//0.21;

        for (int i = 0; i < NUM_TICKS; i++)
        {

	  KF::Matrix t = Qs[i];
          t.setZero();
          t(KF::iBand, KF::iBand) = 0.21; //Just init to smth sensible - will change at run time

        }

        /* Note: Should check that the other entries are 0 by default */

    }

    void initR()
    {

	R.setZero();

        //R(KF::iBand, KF::iBand) = 2;

        R(KF::iBand, KF::iBand) = 0.1; //Experimentally derived


    }


};


