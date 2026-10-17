export default {
  plugins: {
    "postcss-import": {},
    autoprefixer: {},
    ...(process.env.NODE_ENV === "production"
      ? { cssnano: { preset: ["default", { discardComments: { removeAll: true } }] } }
      : {}),
  },
};