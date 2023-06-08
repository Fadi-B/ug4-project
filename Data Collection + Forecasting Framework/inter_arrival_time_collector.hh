#ifndef INTER_ARRIVAL_TIME_HPP
#define INTER_ARRIVAL_TIME_HPP

#include <list>
#include "data_collector.hh"
//#include "filewriter.hh"

using namespace std;

class InterArrivalTimeCollector : public Collector
{

public:

    using Collector::TICK_TIME;
    using Collector::data;
    using Collector::writer;

    /* Curerntly does not have an impact */
    static constexpr double EWMA_WEIGHT = 1.0;

    InterArrivalTimeCollector(double tick_time)
    :Collector(tick_time)
    {

	count = 0;
    ewma_inter_arrival_time = 0;

    }

    Type getType() const override
    {

        return Type::InterArrivalTime;

    }

    void update(double inter_arrival_time, double __attribute((unused)))
    {

        /* Will use less than 0 as indication of 'invalid' and so do not include it */
        if (!(inter_arrival_time < 0))
        {

            helper_data.push_back(inter_arrival_time);

        }


        return;

    }

    double compute()
    {

        /* Used to compute the average */
        double sum_of_inter_arrival_times = 0;
        double inter_arrival_ewma = ewma_inter_arrival_time; //Start from previous value

        double alpha = 1.0/4.0;

        /* Looping until next to last to ensure we do not go out of bounds */
        for (auto it = helper_data.begin(); it != helper_data.end(); it++)
        {

            auto obj = *it;

            sum_of_inter_arrival_times = sum_of_inter_arrival_times + obj;
            inter_arrival_ewma = (1 - alpha) * inter_arrival_ewma + alpha * obj;

        }

        /* Assign it 0 by default */
        double inter_arrival_time = 0;

        uint16_t size = helper_data.size();

        if ( size > 0 && count > 1) //count > 1 to avoid large inter_arrival_time measured due to startup connection
        {

            inter_arrival_time = sum_of_inter_arrival_times / size;

        }

	// NOTE: THIS IS OVERRIDING THE AVERAGE INTER_ARRIVAL_TIME CALCULATION
        inter_arrival_time = inter_arrival_ewma;

        ewma_inter_arrival_time = (1 - EWMA_WEIGHT) * ewma_inter_arrival_time + (EWMA_WEIGHT * inter_arrival_time);

        data.push_back(ewma_inter_arrival_time);

        compute_statistics(ewma_inter_arrival_time, false);

        count = count + 1;

	return ewma_inter_arrival_time;

    }

    void resetHelperData()
    {

        helper_data.clear();

    }

    void resetAll()
    {
        helper_data.clear();
        data.clear();

	    data.push_back(TICK_TIME);

    }

    std::list< double > getHelperData() 
    {
        return helper_data;
    }

    void saveData(std::list<double> &data)
    {

        writer.write_to_file("inter_arrival_data.csv", data);

    }

private:

    uint16_t count;

    std::list< double > helper_data;

    double ewma_inter_arrival_time;

};


#endif

