import type { Category } from '../types';

export const CATEGORIES: { label: string; value: Category }[] = [
  { label: 'Tops', value: 'tops' },
  { label: 'Bottoms', value: 'bottoms' },
  { label: 'Dresses', value: 'dresses' },
  { label: 'Outerwear', value: 'outerwear' },
  { label: 'Shoes', value: 'shoes' },
  { label: 'Accessories', value: 'accessories' },
] as const;

export const SEASONS = [
  { label: 'Spring', value: 'spring' },
  { label: 'Summer', value: 'summer' },
  { label: 'Fall', value: 'fall' },
  { label: 'Winter', value: 'winter' },
  { label: 'All Season', value: 'all-season' },
] as const;

export const OCCASIONS = [
  { label: 'Casual', value: 'casual' },
  { label: 'Work', value: 'work' },
  { label: 'Formal', value: 'formal' },
  { label: 'Sport', value: 'sport' },
  { label: 'Party', value: 'party' },
] as const;

export const COLORS = [
  { label: 'Black', value: 'black', hex: '#000000' },
  { label: 'White', value: 'white', hex: '#FFFFFF' },
  { label: 'Navy', value: 'navy', hex: '#1E3A5F' },
  { label: 'Gray', value: 'gray', hex: '#6B7280' },
  { label: 'Brown', value: 'brown', hex: '#8B4513' },
  { label: 'Beige', value: 'beige', hex: '#F5F5DC' },
  { label: 'Red', value: 'red', hex: '#DC2626' },
  { label: 'Blue', value: 'blue', hex: '#2563EB' },
  { label: 'Green', value: 'green', hex: '#16A34A' },
  { label: 'Pink', value: 'pink', hex: '#EC4899' },
  { label: 'Purple', value: 'purple', hex: '#8B5CF6' },
  { label: 'Yellow', value: 'yellow', hex: '#EAB308' },
  { label: 'Orange', value: 'orange', hex: '#EA580C' },
] as const;

export const PAGE_SIZE = 20;
export const DEBOUNCE_MS = 300;
export const MAX_INPUT_LENGTH = 500;

export type CategoryValue = (typeof CATEGORIES)[number]['value'];
export type SeasonValue = (typeof SEASONS)[number]['value'];
export type OccasionValue = (typeof OCCASIONS)[number]['value'];
