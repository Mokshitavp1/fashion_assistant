import React, { useState, memo } from 'react';
import { Image, View, StyleSheet, ActivityIndicator, ImageStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface Props {
  uri: string | null | undefined;
  style?: ImageStyle;
}

export const LazyImage: React.FC<Props> = memo(({ uri, style }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  if (!uri || error) {
    return (
      <View style={[styles.placeholder, style]}>
        <Ionicons name="image-outline" size={32} color="#D1D5DB" />
      </View>
    );
  }

  return (
    <View>
      {loading && (
        <View style={[styles.loader, style]}>
          <ActivityIndicator size="small" color="#8B5CF6" />
        </View>
      )}
      <Image
        source={{ uri }}
        style={[style, loading && styles.hidden]}
        onLoadEnd={() => setLoading(false)}
        onError={() => setError(true)}
        resizeMode="cover"
      />
    </View>
  );
});

LazyImage.displayName = 'LazyImage';

const styles = StyleSheet.create({
  placeholder: { backgroundColor: '#F3F4F6', justifyContent: 'center', alignItems: 'center' },
  loader: { position: 'absolute', inset: 0, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F3F4F6', zIndex: 1 },
  hidden: { opacity: 0 },
});
