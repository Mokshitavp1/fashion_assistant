import React from 'react';
import { Modal, View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import type { ClothingItem } from '../types';

interface Props {
    item: ClothingItem;
    visible: boolean;
    onClose: () => void;
}

export const ItemDetailModal: React.FC<Props> = ({ item, visible, onClose }) => {
    return (
        <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
            <View style={styles.overlay}>
                <View style={styles.card}>
                    <Text style={styles.title}>{item.item_name || 'Wardrobe Item'}</Text>
                    <Text style={styles.row}>Category: {item.category}</Text>
                    <Text style={styles.row}>Primary Color: {item.color_primary}</Text>
                    <Text style={styles.row}>Season: {item.season}</Text>
                    <TouchableOpacity onPress={onClose} style={styles.button}>
                        <Text style={styles.buttonText}>Done</Text>
                    </TouchableOpacity>
                </View>
            </View>
        </Modal>
    );
};

const styles = StyleSheet.create({
    overlay: {
        flex: 1,
        backgroundColor: 'rgba(0,0,0,0.4)',
        justifyContent: 'flex-end',
    },
    card: {
        backgroundColor: '#fff',
        borderTopLeftRadius: 16,
        borderTopRightRadius: 16,
        padding: 20,
    },
    title: {
        fontSize: 20,
        fontWeight: '700',
        color: '#111827',
        marginBottom: 12,
    },
    row: {
        fontSize: 14,
        color: '#374151',
        marginBottom: 6,
    },
    button: {
        marginTop: 12,
        backgroundColor: '#8B5CF6',
        paddingVertical: 12,
        borderRadius: 10,
        alignItems: 'center',
    },
    buttonText: {
        color: '#fff',
        fontWeight: '600',
    },
});
