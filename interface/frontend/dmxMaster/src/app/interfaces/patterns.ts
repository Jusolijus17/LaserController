export interface Pattern {
  name: string;
  representation?: string;
}

export const PATTERNS: Pattern[] = [
  { name: 'line', representation: '_______' },
  { name: '3 lines', representation: '__ __ __' },
  { name: 'dots', representation: '. . . . .' },
  { name: 'zigzag', representation: '/\\/\\/\\/\\/\\' }
];
