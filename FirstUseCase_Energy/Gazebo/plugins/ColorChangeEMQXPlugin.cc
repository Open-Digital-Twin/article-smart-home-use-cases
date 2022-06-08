#include <gazebo/common/Plugin.hh>
#include "ColorChangeEMQXPlugin.hh"
#include <gazebo/rendering/Visual.hh>
#include <ignition/math/Color.hh>

#include <iostream>
#include <sstream>
#include <vector>
#include <string>
#include "MQTTClient.h"
using namespace std;

#define ADDRESS "tcp://broker.emqx.io:1883"
#define QOS 0
#define TIMEOUT 10000L

using namespace gazebo;

GZ_REGISTER_VISUAL_PLUGIN(ColorChangePlugin)

ColorChangePlugin::ColorChangePlugin()
{

  cout << "ColorChangePlugin init" << endl;
}

ColorChangePlugin::~ColorChangePlugin()
{

  cout << "ColorChangePlugin deinit" << endl;

  MQTTClient_disconnect(this->client, 10000);
  MQTTClient_destroy(&(this->client));
}

void ColorChangePlugin::Load(rendering::VisualPtr _visual, sdf::ElementPtr _sdf)
{

  cout << "view did load" << endl;
  this->visual = _visual;

  MQTTClient_connectOptions conn_opts = MQTTClient_connectOptions_initializer;
  int return_code;
  string topic;

  if (!_sdf->HasElement("topic"))
  {
    return;
  }

  topic = _sdf->Get<string>("topic");

  MQTTClient_create(&client, ADDRESS, topic.c_str(), MQTTCLIENT_PERSISTENCE_NONE, NULL);
  conn_opts.keepAliveInterval = 20;
  conn_opts.cleansession = 1;
  MQTTClient_setCallbacks(client, (void *)this, this->connection_lost_callback, this->message_callback, NULL);
  if ((return_code = MQTTClient_connect(client, &conn_opts)) != MQTTCLIENT_SUCCESS)
  {
    printf("Failed to connect, return code %d\n", return_code);
    exit(EXIT_FAILURE);
  }

  cout << "Subscribing to topic " << topic << " for client " << topic << " using QoS " << QOS << endl;
  MQTTClient_subscribe(client, topic.c_str(), QOS);
}

vector<string> ColorChangePlugin::split_string(const string &s, char delim)
{
  vector<string> result;
  stringstream ss(s);
  string item;

  while (getline(ss, item, delim))
  {
    result.push_back(item);
  }

  return result;
}

void ColorChangePlugin::change_color(char *encoded_message)
{

  vector<string> rgba = this->split_string(encoded_message, '-');
  if (rgba.size() < 4)
  {
    cout << "Invalid file line";
    return;
  }
  cout << "changing color to " << rgba[0] << " " << rgba[1] << " " << rgba[2] << " " << rgba[3] << endl;
  ignition::math::Color color;
  color.Set(stof(rgba[0]), stof(rgba[1]), stof(rgba[2]), stof(rgba[3]));
  this->visual->SetAmbient(color);
}

int ColorChangePlugin::message_callback(void *context, char *topicName, int topicLen, MQTTClient_message *message)
{

  printf("Message arrived\n");
  ColorChangePlugin *_this = (ColorChangePlugin *)context;
  printf("topic: %s\n", topicName);
  printf("message: ");
  char *char_message = (char *)message->payload;
  puts(char_message);
  _this->change_color(char_message);
  MQTTClient_freeMessage(&message);
  MQTTClient_free(topicName);
  return 1;
}

void ColorChangePlugin::connection_lost_callback(void *context, char *cause)
{
  printf("\nConnection lost\n");
  printf("     cause: %s\n", cause);
}
