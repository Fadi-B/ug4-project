#ifndef QUEUING_DELAY_COLLECTOR_HPP
#define QUEUING_DELAY_COLLECTOR_HPP

#include <list>
#include "data_collector.hh"
//#include "filewriter.hh"

using namespace std;

class QueuingDelayCollector : public Collector
{

public:

    using Collector::TICK_TIME;
    using Collector::data;
    using Collector::writer;

    /* Curerntly does not have an impact */
    static constexpr double EWMA_WEIGHT = 1.0;

    QueuingDelayCollector(double tick_time)
    :Collector(tick_time)
    {

        /* Dummy initialization - Update function will do the true updating */
        MIN_RTT = 0;

        /* Assume no delay at the start of connection - reasonable assumption to make */
        queuing_delay = 0;

	/* Assume we start at MIN_RTT*/
        prev_rtt = MIN_RTT;

    }

    Type getType() const override
    {

        return Type::QueueDelay;

    }

    /* NOTE: I am skeptical against what would happen if we get the odd super large RTTs
      
       Does not seem to have appeared yet, but keep an eye as we might have to add an RTT check
    */
    void update(double RTT, double min_rtt)
    {

        helper_data.push_back(RTT);

        /* MIN_RTT can change depending on the time scale we are interested in */
        MIN_RTT = min_rtt;

        return;

    }

    double compute()
    {

        double sum = 0;
        double rtt_ewma = prev_rtt; //start from previous value we had - not working fully - getting negative values

        double alpha = 1.0/4.0;

        for (auto it = helper_data.begin(); it != helper_data.end(); it++)
        {

	    auto obj = *it;

            sum = sum + obj;
            rtt_ewma = (1 - alpha) * rtt_ewma + ( alpha * obj );

        }

        /* Assign it min RTT by default */
        double RTT = MIN_RTT;

        uint16_t size = helper_data.size();

        if ( size > 0)
        {
            /* RTT for this tick will be considered as the average */
            RTT = sum / size;

        }

	//NOTE: THIS IS OVERRIDING THE AVERAGE RTT CALCULATION
        //RTT = rtt_ewma;

        queuing_delay = (1 - EWMA_WEIGHT) * queuing_delay + ( EWMA_WEIGHT * (RTT - MIN_RTT) );

        prev_rtt = rtt_ewma;

        data.push_back(queuing_delay);

        compute_statistics(queuing_delay, false);

	return queuing_delay;

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

        writer.write_to_file("queue_delay_data.csv", data);

    }

private:

    std::list< double > helper_data;

    double MIN_RTT;
    double prev_rtt;

    double queuing_delay;

};


#endif
