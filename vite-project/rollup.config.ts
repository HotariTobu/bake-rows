// rollup.config.ts
import type { RollupOptions } from 'rollup';
import prettier from 'rollup-plugin-prettier';
import typescript from 'rollup-plugin-typescript2';

export default {
  input: 'src/index.ts',
  output: {
    dir: 'dist',
    format: 'esm',
  },
  plugins: [
    typescript(),
    prettier({ parser: 'typescript' }),
  ],
  context: 'this',
} satisfies RollupOptions;
