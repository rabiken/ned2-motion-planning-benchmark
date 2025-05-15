#include <ros/ros.h>
#include <actionlib_msgs/GoalStatusArray.h>
#include <control_msgs/FollowJointTrajectoryActionFeedback.h>
#include <fstream>
#include <vector>
#include "std_srvs/Trigger.h"
#include <chrono>
#include "record_experiment/SetFilename.h"
// #include "niryo_robot_msgs/SetString.h"

class TrajectoryLogger {
    // Private members
    ros::NodeHandle nh_;
    // Ros services
    ros::ServiceServer start_;
    ros::ServiceServer stop_;
    ros::ServiceServer set_filename_;
    bool running;
    std::chrono::steady_clock::time_point start_time;
    // Ros topics
    ros::Subscriber sub_;
    // For writing to file
    std::ofstream file_;
    std::string filename_;
    std::vector<std::string> jointNames_;
    std::vector<double> secA_;
    std::vector<double> nsecA_;
    std::vector<double> secD_;
    std::vector<double> nsecD_;
    std::vector<std::vector<double>> positionsA_;
    std::vector<std::vector<double>> positionsD_;
    std::vector<std::vector<double>> velocitiesD_;
    std::vector<std::vector<double>> accelerationsD_;

    // Private methods
    void feedbackCallback(const control_msgs::FollowJointTrajectoryActionFeedback::ConstPtr& msg) {
        ROS_INFO("Received Follow Joint Trajectory Action Feedback:");
        if (!running) {
            ROS_INFO("Ignoring feedback because logger is not started.");
            return;
        }
        for (size_t i = 0; i < msg->feedback.joint_names.size(); ++i) {
            ROS_INFO("Joint: %s, Position: %f, Velocity: %f",
                     msg->feedback.joint_names[i].c_str(),
                     msg->feedback.desired.positions[i],
                     msg->feedback.desired.velocities[i]);
        }

        jointNames_ = msg->feedback.joint_names;
        secA_.push_back(msg->feedback.actual.time_from_start.sec);
        nsecA_.push_back(msg->feedback.actual.time_from_start.nsec);
        secD_.push_back(msg->feedback.desired.time_from_start.sec);
        nsecD_.push_back(msg->feedback.desired.time_from_start.nsec);
        positionsA_.push_back(msg->feedback.actual.positions);
        positionsD_.push_back(msg->feedback.desired.positions);
        velocitiesD_.push_back(msg->feedback.desired.velocities);
        accelerationsD_.push_back(msg->feedback.desired.accelerations);

    }

    void writeToFile() {
        if (jointNames_.empty()) {
            ROS_WARN("No data to write to file.");
            return;
        }

        file_.open(filename_);

        file_ << "secA,secD,";
        for (size_t i = 0; i < jointNames_.size(); ++i) {
            file_ << jointNames_[i] << "_positionA," 
                << jointNames_[i] << "_positionD," 
                << jointNames_[i] << "_velocityD," 
                << jointNames_[i] << "_accelerationD,";
        }
        file_ << std::endl;

        for(size_t i = 0; i < positionsA_.size(); ++i) {
            file_ << secA_[i]+ 1e-9 * nsecA_[i] << "," 
                << secD_[i]+ 1e-9 * nsecD_[i] << ",";
            for (size_t j = 0; j < jointNames_.size(); ++j) {
                file_ << positionsA_[i][j] << "," 
                    << positionsD_[i][j] << "," 
                    << velocitiesD_[i][j] << "," 
                    << accelerationsD_[i][j] << ",";
            }
            file_ << std::endl;
        }
        // Reset the vector
        jointNames_.clear();
        positionsA_.clear();
        positionsD_.clear();
        velocitiesD_.clear();
        accelerationsD_.clear();
        
        file_.close();
    }

public:
    // Constructor
    TrajectoryLogger(std::string filename = "trajectory_data.csv") 
    : nh_("~") 
    , running(false)
    , filename_(filename)
    {
        ROS_INFO("TrajectoryLogger initialized.");
        start_ = nh_.advertiseService("start", &TrajectoryLogger::startCallback, this);
        stop_ = nh_.advertiseService("stop", &TrajectoryLogger::stopCallback, this);
        set_filename_ = nh_.advertiseService("set_filename", &TrajectoryLogger::setFilenameCallback, this);
        sub_ = nh_.subscribe
            ( "/niryo_robot_follow_joint_trajectory_controller/follow_joint_trajectory/feedback"
            , 10
            , &TrajectoryLogger::feedbackCallback
            , this
            );
    }
    // Start service callback
    bool startCallback(std_srvs::Trigger::Request &req, std_srvs::Trigger::Response &res) {
        if (!running) {
            start_time = std::chrono::steady_clock::now();
            running = true;
            res.success = true;
            res.message = "TrajectoryLogger started.";
        } else {
            res.success = false;
            res.message = "TrajectoryLogger is already running.";
        }
        return true;
    }
    // Stop service callback
    bool stopCallback(std_srvs::Trigger::Request &req, 
                    std_srvs::Trigger::Response &res) {
        if (running) {
            writeToFile();
            auto end_time = std::chrono::steady_clock::now();
            double elapsed_time = std::chrono::duration<double>(end_time - start_time).count();
            running = false;
            res.success = true;
            res.message = "Elapsed time: " + std::to_string(elapsed_time) + " seconds.";
        } else {
            res.success = false;
            res.message = "TrajectoryLogger is not running.";
        }
        return true;
    }

    // Destructor
    ~TrajectoryLogger() {
        if (file_.is_open()) {
            file_.close();
        }
        ROS_INFO("TrajectoryLogger destroyed.");
    }

    // Public methods
    void run() {
        ros::spin();
    }


    void save() {
        writeToFile();
    }


    bool setFilenameCallback(
        // niryo_robot_msgs::SetString::Request &req,
        // niryo_robot_msgs::SetString::Response &res)
        record_experiment::SetFilename::Request &req, 
                        record_experiment::SetFilename::Response &res) 
    {
        filename_ = req.value;
        res.status = true;
        std::string message = "Filename set to: " + filename_;
        res.message = message.c_str();
        return true;
    }

};

int main(int argc, char** argv) {
    ros::init(argc, argv, "trajectory_logger_node");
    TrajectoryLogger logger;
    ros::spin();
    return 0;
}
