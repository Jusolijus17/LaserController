interface Color {
  name: string;
  isMutliColor?: boolean;
}

export const COLORS: Color[] = [
  {
    name: 'multicolor',
    isMutliColor: true
  },
  { name: 'red' },
  { name: 'blue' },
  { name: 'green' },
  { name: 'pink' },
  { name: 'cyan' },
  { name: 'yellow' }
];
