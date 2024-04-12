export interface Pattern {
  name: string;
  representation?: string;
  include: boolean; // Add this line
}

export const PATTERNS: Pattern[] = [
  { name: 'pattern1', representation: '_______', include: true },
  { name: 'pattern2', representation: '__ __ __', include: true },
  { name: 'pattern3', representation: '. . . . .', include: true },
  { name: 'pattern4', representation: '/\\/\\/\\/\\/\\', include: true }
];
