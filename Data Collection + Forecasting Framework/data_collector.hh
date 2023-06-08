#ifndef DATA_COLLECTOR_HPP
#define DATA_COLLECTOR_HPP

#include <list>
#include "filewriter.hh"

#include <numeric>
#include <algorithm>
#include <cmath>

enum class Type {Base, RTTGrad, Packet, QueueDelay, InterArrivalTime};

class Collector
{

public:

    explicit Collector(double tick_time)
    :writer()
    {

        TICK_TIME = tick_time;
        data.push_back(TICK_TIME);

    }

    virtual ~Collector()
    {

    }

    virtual Type getType() const
    {

	return Type::Base;

    }

    virtual void update(double arg1, double arg2) {}

    virtual double compute() {}

    virtual void compute_statistics(double value, bool all) 
    {

        //First element is tick number so exclude it
        uint16_t size = data.size() - 1;

        double new_mean;
        double new_var;

        if (size > 0)
        {
            if (all)
            {
              double sum = std::accumulate(data.begin()++, data.end(), 0.0);
              double mean = sum / size;

              std::vector<double> diff(size);
              std::transform(data.begin()++, data.end(), diff.begin(), [mean](double x) { return x - mean; });
              double sq_sum = std::inner_product(diff.begin(), diff.end(), diff.begin(), 0.0);
              double stdev = std::sqrt(sq_sum / size);

            }
            else
            {
              //Updates mean and std incrementally
              new_mean = _mean + (value - _mean)/size;

              new_var = _var + ((value - _mean)*(value - new_mean));

            }
        }
        else 
        {
            new_mean = 0;
            new_var = 1; //otherwise will break when we normalize
        }

        _mean = new_mean;
        _var = new_var;
    }

    double getMean()
    {
        return _mean;
    }

    double getStd()
    {
//	fprintf(stderr, "Std: %d", _var);
        return std::sqrt(_var);

    }

    virtual void resetHelperData() {}

    void resetAll();

    virtual std::list< double > getData() 
    {
        return data;
    }


    virtual void saveData(std::list<double> &data) {}


protected:

    std::list< double > data;

    double TICK_TIME;

    FileWriter writer;

    double _mean;
    double _var;
    double _prev_mean;

};


#endif

