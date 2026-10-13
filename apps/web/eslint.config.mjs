import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTypeScript from "eslint-config-next/typescript";

export default defineConfig([
  ...nextVitals,
  ...nextTypeScript,
  {
    // Server components catch API transport failures before returning their fallback UI.
    // The rule treats all JSX construction in that narrow try block as render error handling.
    rules: { "react-hooks/error-boundaries": "off" },
  },
  globalIgnores([".next/**", ".next-*/**", "next-env.d.ts"]),
]);
