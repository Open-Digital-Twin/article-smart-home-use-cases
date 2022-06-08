#ifndef COLOR_CHANGE_HH
#define COLOR_CHANGE_HH

#include <gazebo/rendering/Visual.hh>
#include "MQTTClient.h"
#include <sstream>
#include <vector>

using namespace std;

namespace gazebo
{
	class ColorChangePlugin : public VisualPlugin
	{

	public:
		ColorChangePlugin();
		~ColorChangePlugin();
		void Load(rendering::VisualPtr _visual, sdf::ElementPtr _sdf);

	private:
		rendering::VisualPtr visual;
		static int message_callback(void *context, char *topicName, int topicLen, MQTTClient_message *message);
		static void connection_lost_callback(void *context, char *cause);
		void change_color(char *encoded_message);
		vector<string> split_string(const string &s, char delim);
		MQTTClient client;
	};
}
#endif
