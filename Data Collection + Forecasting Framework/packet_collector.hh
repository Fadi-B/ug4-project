#ifndef PACKET_COLLECTOR_HPP
#define PACKET_COLLECTOR_HPP

#include <list>
#include "data_collector.hh"
//#include "filewriter.hh"

using namespace std;

class PacketCollector : public Collector
{

public:

    using Collector::TICK_TIME;
    using Collector::data;
    using Collector::writer;

    static const int MSS = 1400;     /* Bytes */
    static const int BYTE_SIZE = 8;  /* Bits */

    static double to_bits_per_sec(double packets, double tick_time)
    {

        int bits = MSS * BYTE_SIZE;

//        fprintf(stderr, "PACKETS: %f \n", packets);

        double total_bits = packets * (double) bits;

//        fprintf(stderr, "Total Bits: %f \n", total_bits);

        /* Dealing with Mbits/s throughout */
        double Mbits_per_sec = total_bits / ( (double) tick_time*1000);

        return Mbits_per_sec;

    }

    PacketCollector(double tick_time)
    :Collector(tick_time)
    {

    }

    Type getType() const override
    {

        return Type::Packet;

    }

    void update(double packets, double arg2 __attribute((unused)))
    {

        helper_data = helper_data + packets;
//        fprintf(stderr, "COUNT in PackColl: %f \n", helper_data);

        return;

    }

    double compute()
    {

        //fprintf(stderr, "Computing BW for Packets: %f \n", helper_data);

        double Mbits_per_sec = to_bits_per_sec(helper_data, TICK_TIME);

        data.push_back(Mbits_per_sec);

        compute_statistics(Mbits_per_sec, false);

	return Mbits_per_sec;

    }

    void resetHelperData()
    {

        helper_data = 0;

    }

    void resetAll()
    {
        helper_data = 0;
        data.clear();

	    data.push_back(TICK_TIME);
    }

    double getHelperData() 
    {
        return helper_data;
    }

    void saveData(std::list<double> &data)
    {

        writer.write_to_file("throughput_data.csv", data);

    }

private:

    double helper_data;

//    std::list< double > dataf;

//    double TICK_TIME;

};


#endif
