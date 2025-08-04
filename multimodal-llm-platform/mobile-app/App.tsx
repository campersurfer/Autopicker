import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';

// Import screens
import ChatScreen from './src/screens/ChatScreen';
import FilesScreen from './src/screens/FilesScreen';
import SettingsScreen from './src/screens/SettingsScreen';

// Import icons (we'll use text for now, can be replaced with actual icons later)
import { Text } from 'react-native';

const Tab = createBottomTabNavigator();
const queryClient = new QueryClient();

function TabBarIcon({ name, focused }: { name: string; focused: boolean }) {
  const icons: { [key: string]: string } = {
    Chat: '💬',
    Files: '📁',
    Settings: '⚙️',
  };
  
  return (
    <Text style={{ fontSize: 24, opacity: focused ? 1 : 0.6 }}>
      {icons[name] || '📱'}
    </Text>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SafeAreaProvider>
        <NavigationContainer>
          <Tab.Navigator
            screenOptions={({ route }) => ({
              tabBarIcon: ({ focused }) => (
                <TabBarIcon name={route.name} focused={focused} />
              ),
              tabBarActiveTintColor: '#007AFF',
              tabBarInactiveTintColor: '#8E8E93',
              headerStyle: {
                backgroundColor: '#F8F9FA',
              },
              headerTitleStyle: {
                fontWeight: '600',
              },
            })}
          >
            <Tab.Screen 
              name="Chat" 
              component={ChatScreen}
              options={{
                title: 'Multimodal Chat',
                headerTitle: 'AI Assistant',
              }}
            />
            <Tab.Screen 
              name="Files" 
              component={FilesScreen}
              options={{
                title: 'Files',
                headerTitle: 'My Files',
              }}
            />
            <Tab.Screen 
              name="Settings" 
              component={SettingsScreen}
              options={{
                title: 'Settings',
                headerTitle: 'Settings',
              }}
            />
          </Tab.Navigator>
          <StatusBar style="auto" />
        </NavigationContainer>
      </SafeAreaProvider>
    </QueryClientProvider>
  );
}
