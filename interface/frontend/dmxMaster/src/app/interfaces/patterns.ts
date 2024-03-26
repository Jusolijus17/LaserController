export interface Pattern {
  name: string;
  representation?: string;
}

export const PATTERNS: Pattern[] = [
  { name: 'pattern1', representation: '_______' },
  { name: 'pattern2', representation: '__ __ __' },
  { name: 'pattern3', representation: '. . . . .' },
  { name: 'pattern4', representation: '/\\/\\/\\/\\/\\' }
];
