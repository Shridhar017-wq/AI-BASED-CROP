import React from 'react';
import { StyleSheet, SafeAreaView, Platform, StatusBar } from 'react-native';
import { WebView } from 'react-native-webview';

// NOTE: Once you deploy your backend to Render/Heroku, replace this URL with your live URL!
// e.g., const BACKEND_URL = 'https://my-crop-ai.onrender.com';
const BACKEND_URL = 'http://192.168.31.21:5000';

export default function App() {
  return (
    <SafeAreaView style={styles.container}>
      {/* 
        This WebView invisibly loads your entire website backend 
        and renders it as a native feeling app on the phone! 
      */}
      <WebView 
        source={{ uri: BACKEND_URL }} 
        style={styles.webview}
        bounces={false}
        allowsBackForwardNavigationGestures={true}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0
  },
  webview: {
    flex: 1,
  },
});
