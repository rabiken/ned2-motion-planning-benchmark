#include "ros/ros.h"
#include "std_srvs/Trigger.h"
#include <chrono>

class Stopwatch {
private:
    ros::NodeHandle nh;
    ros::ServiceServer start_service;
    ros::ServiceServer stop_service;
    std::chrono::steady_clock::time_point start_time;
    bool running;

public:
    Stopwatch() : nh("~"), running(false) {
        start_service = nh.advertiseService("start_stopwatch", &Stopwatch::startCallback, this);
        stop_service = nh.advertiseService("stop_stopwatch", &Stopwatch::stopCallback, this);
        ROS_INFO("Stopwatch node is ready.");
    }

    bool startCallback(std_srvs::Trigger::Request &req, std_srvs::Trigger::Response &res) {
        if (!running) {
            start_time = std::chrono::steady_clock::now();
            running = true;
            res.success = true;
            res.message = "Stopwatch started.";
        } else {
            res.success = false;
            res.message = "Stopwatch is already running.";
        }
        return true;
    }

    bool stopCallback(std_srvs::Trigger::Request &req, std_srvs::Trigger::Response &res) {
        if (running) {
            auto end_time = std::chrono::steady_clock::now();
            double elapsed_time = std::chrono::duration<double>(end_time - start_time).count();
            running = false;
            res.success = true;
            res.message = "Elapsed time: " + std::to_string(elapsed_time) + " seconds.";
        } else {
            res.success = false;
            res.message = "Stopwatch is not running.";
        }
        return true;
    }
};

int main(int argc, char **argv) {
    ros::init(argc, argv, "stopwatch_node");
    Stopwatch stopwatch;
    ros::spin();
    return 0;
}
