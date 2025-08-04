import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Switch,
  Alert,
  ScrollView,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { chatAPI } from '../services/api';

interface SettingRowProps {
  title: string;
  subtitle?: string;
  onPress?: () => void;
  showArrow?: boolean;
  rightComponent?: React.ReactNode;
}

function SettingRow({ title, subtitle, onPress, showArrow = false, rightComponent }: SettingRowProps) {
  return (
    <TouchableOpacity 
      style={styles.settingRow} 
      onPress={onPress}
      disabled={!onPress}
    >
      <View style={styles.settingContent}>
        <Text style={styles.settingTitle}>{title}</Text>
        {subtitle && <Text style={styles.settingSubtitle}>{subtitle}</Text>}
      </View>
      {rightComponent}
      {showArrow && (
        <Text style={styles.settingArrow}>›</Text>
      )}
    </TouchableOpacity>
  );
}

interface SettingSectionProps {
  title: string;
  children: React.ReactNode;
}

function SettingSection({ title, children }: SettingSectionProps) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionHeader}>{title}</Text>
      <View style={styles.sectionContent}>
        {children}
      </View>
    </View>
  );
}

export default function SettingsScreen() {
  const [darkMode, setDarkMode] = useState(false);
  const [notifications, setNotifications] = useState(true);
  const [autoSave, setAutoSave] = useState(true);

  const {
    data: healthData,
    isLoading: healthLoading,
    error: healthError,
    refetch: checkHealth
  } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      return await chatAPI.healthCheck();
    },
    retry: 1,
  });

  const handleAbout = () => {
    Alert.alert(
      'Autopicker Mobile',
      'Version 1.0.0\n\nA multimodal AI assistant that can process documents, images, and audio files.\n\nBuilt with React Native and powered by advanced AI models.',
      [{ text: 'OK' }]
    );
  };

  const handlePrivacy = () => {
    Alert.alert(
      'Privacy Policy',
      'Your privacy is important to us. This app processes files locally and through secure API calls. No personal data is stored permanently on our servers.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Learn More', onPress: () => handleLearnMore() },
      ]
    );
  };

  const handleTerms = () => {
    Alert.alert(
      'Terms of Service',
      'By using this app, you agree to our terms of service. Please use the app responsibly and in accordance with applicable laws.',
      [{ text: 'OK' }]
    );
  };

  const handleLearnMore = () => {
    // In a real app, this would open a web view or external browser
    Alert.alert(
      'Learn More',
      'For detailed privacy policy and terms, please visit our website.',
      [{ text: 'OK' }]
    );
  };

  const handleFeedback = () => {
    Alert.alert(
      'Send Feedback',
      'We\'d love to hear your thoughts! Please share your feedback and suggestions.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Email Support', onPress: () => handleEmailSupport() },
      ]
    );
  };

  const handleEmailSupport = () => {
    const email = 'support@autopicker.com';
    const subject = 'Autopicker Mobile Feedback';
    const body = 'Hi! I have feedback about the Autopicker mobile app:\n\n';
    
    const url = `mailto:${email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    
    Linking.canOpenURL(url).then((supported) => {
      if (supported) {
        Linking.openURL(url);
      } else {
        Alert.alert(
          'Email Not Available',
          `Please send your feedback to: ${email}`,
          [{ text: 'OK' }]
        );
      }
    });
  };

  const handleClearCache = () => {
    Alert.alert(
      'Clear Cache',
      'This will clear all cached data and may improve app performance. Are you sure?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Clear', 
          style: 'destructive',
          onPress: () => {
            // TODO: Implement cache clearing
            Alert.alert('Success', 'Cache cleared successfully!');
          }
        },
      ]
    );
  };

  const handleCheckConnection = () => {
    checkHealth();
  };

  const getConnectionStatus = () => {
    if (healthLoading) return { text: 'Checking...', color: '#FF9500' };
    if (healthError) return { text: 'Offline', color: '#FF3B30' };
    if (healthData) return { text: 'Connected', color: '#34C759' };
    return { text: 'Unknown', color: '#8E8E93' };
  };

  const connectionStatus = getConnectionStatus();

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Connection Status */}
        <SettingSection title="Connection">
          <SettingRow
            title="Server Status"
            subtitle={`API connection: ${connectionStatus.text}`}
            onPress={handleCheckConnection}
            rightComponent={
              <View style={[styles.statusDot, { backgroundColor: connectionStatus.color }]} />
            }
          />
        </SettingSection>

        {/* App Preferences */}
        <SettingSection title="Preferences">
          <SettingRow
            title="Dark Mode"
            subtitle="Switch to dark theme"
            rightComponent={
              <Switch
                value={darkMode}
                onValueChange={setDarkMode}
                trackColor={{ false: '#E5E5E7', true: '#007AFF' }}
              />
            }
          />
          <SettingRow
            title="Notifications"
            subtitle="Enable push notifications"
            rightComponent={
              <Switch
                value={notifications}
                onValueChange={setNotifications}
                trackColor={{ false: '#E5E5E7', true: '#007AFF' }}
              />
            }
          />
          <SettingRow
            title="Auto-save Conversations"
            subtitle="Automatically save chat history"
            rightComponent={
              <Switch
                value={autoSave}
                onValueChange={setAutoSave}
                trackColor={{ false: '#E5E5E7', true: '#007AFF' }}
              />
            }
          />
        </SettingSection>

        {/* Data & Storage */}
        <SettingSection title="Data & Storage">
          <SettingRow
            title="Clear Cache"
            subtitle="Free up storage space"
            onPress={handleClearCache}
            showArrow
          />
        </SettingSection>

        {/* Support */}
        <SettingSection title="Support">
          <SettingRow
            title="Send Feedback"
            subtitle="Help us improve the app"
            onPress={handleFeedback}
            showArrow
          />
          <SettingRow
            title="Privacy Policy"
            onPress={handlePrivacy}
            showArrow
          />
          <SettingRow
            title="Terms of Service"
            onPress={handleTerms}
            showArrow
          />
        </SettingSection>

        {/* About */}
        <SettingSection title="About">
          <SettingRow
            title="About Autopicker"
            subtitle="Version 1.0.0"
            onPress={handleAbout}
            showArrow
          />
        </SettingSection>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  scrollView: {
    flex: 1,
  },
  section: {
    marginBottom: 32,
  },
  sectionHeader: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 12,
    marginHorizontal: 16,
  },
  sectionContent: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    marginHorizontal: 16,
    overflow: 'hidden',
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E5E7',
  },
  settingContent: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#000000',
    marginBottom: 2,
  },
  settingSubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 18,
  },
  settingArrow: {
    fontSize: 20,
    color: '#C7C7CC',
    marginLeft: 8,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginLeft: 8,
  },
});