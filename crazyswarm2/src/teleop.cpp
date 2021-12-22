#include <memory>
#include <vector>
#include <chrono>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/joy.hpp"
#include "std_srvs/srv/empty.hpp"
#include "crazyswarm2_interfaces/srv/takeoff.hpp"
#include "crazyswarm2_interfaces/srv/land.hpp"
#include "geometry_msgs/msg/twist.hpp"


using std::placeholders::_1;

using std_srvs::srv::Empty;
using crazyswarm2_interfaces::srv::Takeoff;
using crazyswarm2_interfaces::srv::Land;

using namespace std::chrono_literals;


namespace Xbox360Buttons {

    enum { Green = 0,
           Red = 1,
           Blue = 2,
           Yellow = 3,
           LB = 4,
           RB = 5,
           Back = 6,
           Start = 7,
           COUNT = 8,
    };
}

class TeleopNode : public rclcpp::Node
{
public:
    TeleopNode()
        : Node("teleop")
    {
        
        subscription_ = this->create_subscription<sensor_msgs::msg::Joy>(
            "joy", 1, std::bind(&TeleopNode::joyChanged, this, _1));

        publisher_ = this->create_publisher<geometry_msgs::msg::Twist>("cmd_vel", 10);
        
        this->declare_parameter<int>("frequency", 1);
        frequency_ = this->get_parameter("frequency").as_int();
        this->declare_parameter<int>("axes_x", 4);
        axes_.x = this->get_parameter("axes_x").as_int();
        this->declare_parameter<int>("axes_y", 3);
        axes_.y = this->get_parameter("axes_y").as_int();
        this->declare_parameter<int>("axes_z", 2);
        axes_.z = this->get_parameter("axes_z").as_int();
        this->declare_parameter<int>("axes_yaw", 1);
        axes_.yaw = this->get_parameter("axes_yaw").as_int();

        timer_ = this->create_wall_timer(
            std::chrono::seconds(1/frequency_),
            std::bind(&TeleopNode::publish, this));

       

        // client_emergency_ = this->create_client<Empty>("emergency");
        // client_emergency_->wait_for_service();

        // client_takeoff_ = this->create_client<Takeoff>("takeoff");
        // client_takeoff_->wait_for_service();

        // client_land_ = this->create_client<Land>("land");
        // client_land_->wait_for_service();
        
    }

private:
    struct
    {
        int x;
        int y;
        int z;
        int yaw;
    } axes_;

    void publish() 
    {
        publisher_->publish(twist_);
            
    }

    void joyChanged(const sensor_msgs::msg::Joy::SharedPtr msg)
    {

        static std::vector<int> lastButtonState(Xbox360Buttons::COUNT);

        if (msg->buttons.size() >= Xbox360Buttons::COUNT && lastButtonState.size() >= Xbox360Buttons::COUNT) {
            if (msg->buttons[Xbox360Buttons::Red] == 1 && lastButtonState[Xbox360Buttons::Red] == 0) {
                emergency();
            }
            if (msg->buttons[Xbox360Buttons::Start] == 1 && lastButtonState[Xbox360Buttons::Start] == 0) {
                takeoff();
            }
            if (msg->buttons[Xbox360Buttons::Back] == 1 && lastButtonState[Xbox360Buttons::Back] == 0) {
                land();
            }
        }

        lastButtonState = msg->buttons;
        
        twist_.linear.x = getAxis(msg, axes_.x);
        twist_.linear.y = getAxis(msg, axes_.y);
        twist_.linear.z = getAxis(msg, axes_.z);
        twist_.angular.z = getAxis(msg, axes_.yaw);
    }

    sensor_msgs::msg::Joy::_axes_type::value_type getAxis(const sensor_msgs::msg::Joy::SharedPtr &msg, int axis)
    {
        if (axis == 0) {
            return 0;
        }

        sensor_msgs::msg::Joy::_axes_type::value_type sign = 1.0;
        if (axis < 0) {
            sign = -1.0;
            axis = -axis;
        }
        if ((size_t) axis > msg->axes.size()) {
            return 0;
        }
        return sign * msg->axes[axis - 1]*2;
    }

    
    void emergency()
    {
        RCLCPP_INFO(this->get_logger(), "emergency requested...");
        auto request = std::make_shared<Empty::Request>();
        auto result = client_emergency_->async_send_request(request);
        rclcpp::spin_until_future_complete(this->get_node_base_interface(), result);
        RCLCPP_INFO(this->get_logger(), "Done.");
    }

    void takeoff()
    {
        auto request = std::make_shared<Takeoff::Request>();
        request->group_mask = 0;
        request->height = 0.5;
        request->duration = rclcpp::Duration::from_seconds(2);
        auto result = client_takeoff_->async_send_request(request);
        rclcpp::spin_until_future_complete(this->get_node_base_interface(), result);
    }

    void land()
    {
        auto request = std::make_shared<Land::Request>();
        request->group_mask = 0;
        request->height = 0.0;
        request->duration = rclcpp::Duration::from_seconds(3.5);
        auto result = client_land_->async_send_request(request);
        rclcpp::spin_until_future_complete(this->get_node_base_interface(), result);
    }

    rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr subscription_;
    rclcpp::Client<std_srvs::srv::Empty>::SharedPtr client_emergency_;
    rclcpp::Client<Takeoff>::SharedPtr client_takeoff_;
    rclcpp::Client<Land>::SharedPtr client_land_;
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
    geometry_msgs::msg::Twist twist_;
    int frequency_;
    
};

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<TeleopNode>());
    rclcpp::shutdown();
    return 0;
}
