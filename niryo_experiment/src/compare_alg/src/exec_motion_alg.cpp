/**
 * @file exec_motion_alg5.cpp
 * @author Riku Kawasaki (kawasrik@fit.cvut.cz)
 * @brief 
 * @version 0.1
 * @date 2025-04-04
 * 
 * @copyright Copyright (c) 2025
 * 
 */
#include <moveit/move_group_interface/move_group_interface.h>
#include <moveit/planning_scene_interface/planning_scene_interface.h>
#include <moveit_msgs/AttachedCollisionObject.h>
#include <moveit_msgs/CollisionObject.h>
#include <fstream>
#include <niryo_robot_sound/TextToSpeech.h>
#include <std_srvs/Trigger.h>
#include "record_experiment/SetFilename.h"
#include <ros/ros.h>
#include <vector>
#include <string>
#include <map>


bool speakEnglish( ros::ServiceClient & speech_client,
           niryo_robot_sound::TextToSpeech & speech_srv, 
           const std::string text  ) 
{
  speech_srv.request.text = text;
  speech_srv.request.language = 0; // English
  if (speech_client.call(speech_srv)) {
    ROS_INFO("SPEECH SRV WAS SUCCESSFULLY CALLED.");
    return true;
  } else {
    ROS_INFO("SPEECH SRV WASN'T CALLED SUCCESFULLY.");
  }
  return false;
}

class Speaker {
public:
  ros::ServiceClient* m_client = nullptr;
  niryo_robot_sound::TextToSpeech* m_srv = nullptr;
  int m_language = 0;
  bool m_enabled = true;
public:
  // Constructor
  Speaker(ros::NodeHandle& nh, int language = 0) 
  {
    nh.getParam("experiment_config/enable_speech", m_enabled);
    ROS_INFO("Speaker initialized.");
    m_language = language;
    m_client = new ros::ServiceClient(
        nh.serviceClient<niryo_robot_sound::TextToSpeech>("/niryo_robot_sound/text_to_speech") );
    m_srv = new niryo_robot_sound::TextToSpeech();
  }
  // Destructor
  ~Speaker() {
    delete m_srv;
    delete m_client;
    m_srv = nullptr;
    m_client = nullptr;
    ROS_INFO("Speaker destroyed.");
  }

  bool speak(const std::string & text) {
    if (!m_enabled) {
      ROS_INFO("(no voice) %s", text.c_str());
      return true;
    }
    m_srv->request.text = text;
    m_srv->request.language = m_language; // English
    if (m_client->call(*m_srv)) {
      ROS_INFO("(voice) %s", text.c_str());
      return true;
    } else {
      ROS_INFO("SPEECH SRV WASN'T CALLED SUCCESFULLY.");
      return false;
    }
    return true;
  }
};

class Recorder {
public:
  ros::ServiceClient m_set_filename_client;
  ros::ServiceClient m_start_client;
  ros::ServiceClient m_stop_client;
  record_experiment::SetFilename m_set_filename_srv;
  std_srvs::Trigger m_start_srv;
  std_srvs::Trigger m_stop_srv;
public:
  // Constructor
  Recorder(ros::NodeHandle& nh)
  : m_set_filename_client(nh.serviceClient<record_experiment::SetFilename>("/trajectory_logger_node/set_filename"))
  , m_start_client(nh.serviceClient<std_srvs::Trigger>("/trajectory_logger_node/start"))
  , m_stop_client(nh.serviceClient<std_srvs::Trigger>("/trajectory_logger_node/stop"))
  , m_set_filename_srv()
  , m_start_srv()
  , m_stop_srv()
  {
    ROS_INFO("Recorder initialized.");
  }
  // Destructor
  ~Recorder() {
    ROS_INFO("Recorder destroyed.");
  }
  bool setFilename(const std::string & filename) {
    ROS_INFO("Setting filename: %s", filename.c_str());
    m_set_filename_srv.request.value = filename;
    if ( ! m_set_filename_client.call(m_set_filename_srv) ) {
      ROS_ERROR("/trajectory_logger_node says: %s", m_set_filename_srv.response.message.c_str());
      return false;
    }
    return true;
  }
  bool startRecording() {
    return m_start_client.call(m_start_srv);
  }
  bool stopRecording() {
    return m_stop_client.call(m_stop_srv);
  }
  bool outputPlanningTime(const std::string & filename, const double& planning_time)const {
    std::ofstream ofs(filename.c_str());
    if (!ofs) {
      ROS_ERROR("Failed to open file: %s", filename.c_str());
      return false;
    }
    ofs << planning_time << std::endl;
    ofs.close();
    return true;
  }
  
};

class Planner {
public:
  moveit::planning_interface::MoveGroupInterface m_move_group_interface;
  moveit::planning_interface::PlanningSceneInterface m_planning_scene_interface;
  const moveit::core::JointModelGroup* m_joint_model_group;
  moveit::planning_interface::MoveGroupInterface::Plan m_plan;
  double m_max_velocity_scaling_factor;
  double m_max_acceleration_scaling_factor;
  double m_max_planning_time;
public:
  // Constructor
  Planner(ros::NodeHandle& nh, 
          const std::string & planning_group, 
          const double max_planning_time = 5.0, 
          const double max_velocity_scaling_factor = 1.0, 
          const double max_acceleration_scaling_factor = 1.0)
  : m_move_group_interface(planning_group)
  , m_planning_scene_interface()
  , m_joint_model_group(m_move_group_interface.getCurrentState()->getJointModelGroup(planning_group))
  {
    this->setMaxPlanningTime(max_planning_time);
    this->setMaxVelocityScalingFactor(max_velocity_scaling_factor);
    this->setMaxAccelerationScalingFactor(max_acceleration_scaling_factor);
    ROS_INFO("Planner initialized.");
  }
  // Destructor
  ~Planner() {
    ROS_INFO("Planner destroyed.");
  }
  bool plan(const std::vector<double> & target, double& planning_time) {
    m_move_group_interface.setJointValueTarget(target);
    bool success = (m_move_group_interface.plan(m_plan) == moveit::core::MoveItErrorCode::SUCCESS);
    planning_time = m_plan.planning_time_;
    ROS_INFO("Planning time: %f", planning_time);
    return success;
  }
  bool setPlannerId(const std::string & planner_id) {
    m_move_group_interface.setPlannerId(planner_id);
    return true;
  }
  std::string getPlannerId() const {
    return m_move_group_interface.getPlannerId();
  }
  bool execute() {
    bool success = (m_move_group_interface.execute(m_plan) == moveit::core::MoveItErrorCode::SUCCESS);
    ROS_INFO("Execution %s", success ? "succeeded" : "failed");
    return success;
  }
  bool moveTo(const std::vector<double> & target) {
    m_move_group_interface.setJointValueTarget(target);
    bool success = (m_move_group_interface.move() == moveit::core::MoveItErrorCode::SUCCESS);
    ROS_INFO("Move to %s", success ? "succeeded" : "failed");
    return success;
  }
  // DO NOT USE THIS FUNCTION: After this function, the move_group node will be lost for some reason.
  // It is not clear why this happens, but it is better to use the moveTo function instead.
  bool moveTo_with_best(const std::vector<double> & target) {
    // get the current settings
    const double tmp_max_planning_time = m_max_planning_time;
    const double tmp_max_velocity_scaling_factor = m_max_velocity_scaling_factor;;
    const double tmp_max_acceleration_scaling_factor = m_max_acceleration_scaling_factor;;
    const std::string tmp_planner_id = getPlannerId();
    // set the planner id
    setPlannerId("PRMkConfigDefault");
    // set the new settings
    setMaxPlanningTime(15.0); // 15 sec
    setMaxVelocityScalingFactor(0.5); // 50% of max velocity
    setMaxAccelerationScalingFactor(0.5); // 50% of max acceleration
    // plan the motion
    bool success = this->moveTo(target);
    // set the old settings
    setPlannerId(tmp_planner_id);
    setMaxPlanningTime(tmp_max_planning_time);
    setMaxVelocityScalingFactor(tmp_max_velocity_scaling_factor);
    setMaxAccelerationScalingFactor(tmp_max_acceleration_scaling_factor);
    return success;
  }
  bool setMaxVelocityScalingFactor(double factor) {
    m_max_velocity_scaling_factor = factor;
    m_move_group_interface.setMaxVelocityScalingFactor(factor);
    return true;
  }
  bool setMaxAccelerationScalingFactor(double factor) {
    m_max_acceleration_scaling_factor = factor;
    m_move_group_interface.setMaxAccelerationScalingFactor(factor);
    return true;
  }
  double getMaxVelocityScalingFactor() const {
    return m_max_velocity_scaling_factor;
 }
  double getMaxAccelerationScalingFactor() const {
    return m_max_acceleration_scaling_factor;
  }
  bool setMaxPlanningTime(double time) {
    m_max_planning_time = time;
    m_move_group_interface.setPlanningTime(time);
    return true;
  }
  double getMaxPlanningTime() const {
    double time = m_move_group_interface.getPlanningTime();
    return time;
  }
  
};

class ExperimentManager {
public:
  ros::NodeHandle& m_nh;
  Recorder m_recorder;
  Speaker m_speaker;
  Planner m_planner;
  std::vector<double> m_planning_times;
public:
  // Constructor
  ExperimentManager(ros::NodeHandle& nh, const std::string & planning_group)
  : m_nh(nh)
  , m_recorder(nh)
  , m_speaker(nh)
  , m_planner(nh, planning_group)
  {
    // MoveIt operates on sets of joints called "planning groups" and stores them in an object called
    // the `JointModelGroup`. Throughout MoveIt the terms "planning group" and "joint model group"
    // are used interchangeably.
    ROS_INFO("ExperimentManager initialized.");
  }
  // Destructor
  ~ExperimentManager() {
    // leave the archive of the planning times just in case
    std::string planning_time_filename = "/tmp/planning_times.csv";
    std::ofstream ofs(planning_time_filename.c_str());
    if (!ofs) {
      ROS_ERROR("Failed to open file: %s", planning_time_filename.c_str());
    } else {
      ofs << "Planning time" << std::endl;
      for (size_t i = 0; i < m_planning_times.size(); ++i) {
        ofs << m_planning_times[i] << std::endl;
      }
      ofs.close();
    }
    // Leave the recorder and planner to be destroyed by the destructor
    ROS_INFO("ExperimentManager destroyed.");
  }
  bool waitManualRestart() {
    // Wait for the stop parameter to be false
    bool param = true;
    // m_nh.setParam("pose_experiment", param);
    ros::param::set("pose_experiment", param);
    // Manually run "rosparam set /<namespace>/pose_experiment false"
    m_speaker.speak("Manual navigation is required.");
    while (ros::ok() && ros::param::get("pose_experiment", param) && param==true) {
      ROS_INFO("Waiting for the stop parameter to be false.");
      ros::Duration(1.0).sleep();
    }
    m_speaker.speak("Restarting experiment.");
    return true;
  }
  std::string doubleToString(const double& value, const int precision = 2) const {
    std::ostringstream oss;
    oss.precision(precision);
    oss << std::fixed << value;
    return oss.str();
  }

  bool runExperiment( const double max_planning_time, 
                    const double& max_velocity_scaling_factor,
                    const double& max_acceleration_scaling_factor,
                    const std::vector<double> & start_pose, 
                    const std::vector<double> & goal_pose,
                    const std::string & planner_id,
                    const std::string & dir_name, 
                    const std::string & filename_base,
                    const int id,
                    const std::string & starting_speech = "Planning motion" ) 
  {
    // Start experiment
    m_planner.setPlannerId(planner_id);
    // Set max planning time
    m_planner.setMaxPlanningTime(max_planning_time);
    // Set max velocity scaling factor
    m_planner.setMaxVelocityScalingFactor(max_velocity_scaling_factor);
    // Set max acceleration scaling factor
    m_planner.setMaxAccelerationScalingFactor(max_acceleration_scaling_factor);


    // Move to start_pose
    if ( dir_name.empty() || filename_base.empty() ) {
      ROS_ERROR("Please make sure to set the directory name and filename base.");
      return false;
    }
    // Wait for 0.5 sec
    ros::Duration(0.5).sleep();

    bool success = m_planner.moveTo(start_pose);
    while (!success) {
      ROS_INFO("Failed to move to start_pose. Retrying...");
      waitManualRestart();
      success = m_planner.moveTo(start_pose);
    }

    // Speak the starting speech
    m_speaker.speak(starting_speech);
    // Move to goal_pose
    double planning_time;
    // std::string planning_time_filename = dir_name + "/" + filename_base + std::to_string(id) + "_time.txt";
    // Plan the motion
    success = m_planner.plan(goal_pose, planning_time) == moveit::core::MoveItErrorCode::SUCCESS;
    if (success)
    {
      m_speaker.speak("Planning succeeded.");
      ROS_INFO("Planning succeeded.");
    }
    else  {
      m_speaker.speak("Failed to plan.");
      ROS_INFO("Failed to plan.");
      // m_recorder.outputPlanningTime(planning_time_filename, -1.0);
      m_planning_times.push_back(-1.0);
      return true;
    }
    // Remember the planning time
    // if (!m_recorder.outputPlanningTime(planning_time_filename, planning_time)) {
    //   ROS_ERROR("Failed to output planning time.");
    //   return false;
    // }
    m_planning_times.push_back(planning_time);
    // Set the filename
    std::string filename = dir_name + "/" + filename_base + "_" + std::to_string(id) + ".csv";
    if (!m_recorder.setFilename(filename)) {
      ROS_ERROR("Failed to set filename.");
      return false;
    }
    // Start recording
    if (!m_recorder.startRecording()) {
      ROS_ERROR("Failed to start recording.");
      return false;
    }
    // Wait for 0.5 sec
    ros::Duration(0.5).sleep();
    // Move to the target
    if (!m_planner.execute()) {
      ROS_ERROR("Failed to execute.");
      return false;
    }
    // Stop recording
    if (!m_recorder.stopRecording()) {
      ROS_ERROR("Failed to stop recording.");
      return false;
    }
    return true;
  }
  bool iterateExperiment(const int num_iterations, 
                        const double max_planning_time, 
                        const double& max_velocity_scaling_factor,
                        const double& max_acceleration_scaling_factor,
                        const std::vector<double> & start_pose, 
                        const std::vector<double> & goal_pose, 
                        const std::string & planner_id, 
                        const std::string & dir_name, 
                        const std::string & filename_base ) 
  {
    m_planner.setPlannerId(planner_id);
    m_planner.setMaxPlanningTime(max_planning_time);
    m_planner.setMaxVelocityScalingFactor(max_velocity_scaling_factor);
    m_planner.setMaxAccelerationScalingFactor(max_acceleration_scaling_factor);

    m_speaker.speak(planner_id + " is selected.");
    m_speaker.speak("Max planning time: " + doubleToString(max_planning_time, 0) + " seconds");
    m_speaker.speak("Max velocity scaling factor: " + doubleToString(max_velocity_scaling_factor, 1));
    m_speaker.speak("Max acceleration scaling factor: " + doubleToString(max_acceleration_scaling_factor, 1));

    m_speaker.speak("Number of iterations: " + std::to_string(num_iterations));
    // Iterate over the number of iterations
    for (int i = 0; i < num_iterations; ++i) {
      // Run the experiment
      // m_speaker.speak("Iteration " + std::to_string(i) );
      const std::string iteration_speech = "Iteration " + std::to_string(i);
      bool success = runExperiment(max_planning_time, 
                max_velocity_scaling_factor, 
                max_acceleration_scaling_factor, 
                start_pose, 
                goal_pose, 
                planner_id, 
                dir_name, 
                filename_base, 
                i,
                iteration_speech);
      if (!success) {
        ROS_ERROR("Failed to run experiment. iteration:%d", i);
        return false;
      }
    }
    // Output the planning times
    std::string planning_time_filename = dir_name + "/" + filename_base + "_time.csv";
    std::ofstream ofs(planning_time_filename.c_str());
    if (!ofs) {
      ROS_ERROR("Failed to open file: %s", planning_time_filename.c_str());
      return false;
    }
    ofs << "Planning time" << std::endl;
    for (size_t i = 0; i < m_planning_times.size(); ++i) {
      ofs << m_planning_times[i] << std::endl;
    }
    return true;
  }

};

int main(int argc, char** argv)
{
  // Initialize ros
  ros::init(argc, argv, "exec_motion_alg5");
  // Define the node handle
  ros::NodeHandle nh("~");
  // ROS spinning must be running for the MoveGroupInterface to get information
  // about the robot's state. One way to do this is to start an AsyncSpinner
  // beforehand.
  ros::AsyncSpinner spinner(1);
  spinner.start();
  
  // Wait for 5 second to make sure another node is up
  ros::Duration(5.0).sleep();

  // Create the ExperimentManager object
  const std::string planning_group = "arm";
  ExperimentManager expr_manager(nh, planning_group);
  expr_manager.m_speaker.speak("Initializing experiment.");

  // Initialize Experiment
  // Read nested parameters under "experiment_config"
  std::vector<double> init_pose, start_pose, goal_pose;
  double max_planning_time;
  double max_velocity_scaling_factor;
  double max_acceleration_scaling_factor;
  int planning_attempts;
  std::string planner_id;
  int num_iterations;
  std::string dir_name;
  std::string config_file_path;

  // Load init_pose, start_pose, and goal_pose
  if (nh.getParam("experiment_config/init_pose", init_pose) &&
      nh.getParam("experiment_config/start_pose", start_pose) &&
      nh.getParam("experiment_config/goal_pose", goal_pose)) {
      
      ROS_INFO("Init Pose: [%f, %f, %f, %f, %f, %f]", 
                init_pose[0], init_pose[1], init_pose[2], 
                init_pose[3], init_pose[4], init_pose[5]);

      ROS_INFO("Start Pose: [%f, %f, %f, %f, %f, %f]", 
                start_pose[0], start_pose[1], start_pose[2], 
                start_pose[3], start_pose[4], start_pose[5]);

      ROS_INFO("Goal Pose: [%f, %f, %f, %f, %f, %f]", 
                goal_pose[0], goal_pose[1], goal_pose[2], 
                goal_pose[3], goal_pose[4], goal_pose[5]);
  } else {
      ROS_ERROR("Failed to load poses from experiment_config!");
      return -1;
  }

  // Load other parameters
  if (nh.getParam("experiment_config/max_planning_time", max_planning_time)) {
      ROS_INFO("Planning Time: %f", max_planning_time);
  }

  if (nh.getParam("experiment_config/planning_attempts", planning_attempts)) {
      ROS_INFO("Planning Attempts: %d", planning_attempts);
  }

  if (nh.getParam("experiment_config/planner_id", planner_id)) {
      ROS_INFO("Planner ID: %s", planner_id.c_str());
  }

  if (nh.getParam("experiment_config/num_iterations", num_iterations)) {
      ROS_INFO("Number of iterations: %d", num_iterations);
  }

  if (nh.getParam("experiment_config/dir_name", dir_name)) {
      ROS_INFO("Directory name: %s", dir_name.c_str());
  }

  if (nh.getParam("experiment_config/config_file_path", config_file_path)) {
      ROS_INFO("Config file path: %s", config_file_path.c_str());
  }

  if (nh.getParam("experiment_config/max_velocity_scaling_factor", max_velocity_scaling_factor)) {
      ROS_INFO("Max velocity scaling factor: %f", max_velocity_scaling_factor);
  }

  if (nh.getParam("experiment_config/max_acceleration_scaling_factor", max_acceleration_scaling_factor)) {
      ROS_INFO("Max acceleration scaling factor: %f", max_acceleration_scaling_factor);
  }
  
  const std::string filename_base = planner_id;
  
  // Copy the experiment configuration to a file
  std::string config_out_file = dir_name + "/" + filename_base + "_experiment_config.yaml";
  std::ofstream ofs(config_out_file.c_str());
  if ( !ofs) {
    ROS_ERROR("Failed to open file: %s", config_out_file.c_str());
    return -1;
  }
  std::ifstream ifs(config_file_path.c_str());
  if ( !ifs) {
    ROS_ERROR("Failed to open file: %s", config_file_path.c_str());
    return -1;
  }
  ofs << ifs.rdbuf();
  ofs.close();
  ifs.close();
  ROS_INFO("Experiment configuration saved to %s", config_out_file.c_str());

  // Start experiment
  expr_manager.m_speaker.speak( "Starting experiment.");
  bool success = false;
  
  success = expr_manager.iterateExperiment(
      num_iterations, 
      max_planning_time,
      max_velocity_scaling_factor,
      max_acceleration_scaling_factor,
      start_pose, 
      goal_pose, planner_id, dir_name, filename_base);

  if ( ! success ) {
    expr_manager.m_speaker.speak( "Experiment failed.");
    return -1;
  }

  // Finish Experiment
  expr_manager.m_speaker.speak( "Experiment completed.");

  expr_manager.m_speaker.speak( "Moving to the resting position.");
  success = expr_manager.m_planner.moveTo(init_pose);

  ROS_INFO_NAMED("tutorial", "Moved to the starting pose %s", success ? "" : "FAILED");
  if ( success ) {
    expr_manager.m_speaker.speak( "Done. Ending experiment.");
  } else {
    expr_manager.m_speaker.speak( "Failed. Ending experiment.");
  }

  ros::shutdown();
  return 0;
}
