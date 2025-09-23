const path = require('path');

module.exports = {
  // ... other config
  performance: {
    hints: false, // Disable performance hints
    maxEntrypointSize: 2048000, // 2MB (increased from 512KB)
    maxAssetSize: 2048000, // 2MB (increased from 512KB)
  },
  resolve: {
    alias: {
      '@mui/icons-material': path.resolve(__dirname, 'node_modules/@mui/icons-material'),
    },
  },
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
        mui: {
          test: /[\\/]node_modules[\\/]@mui[\\/]/,
          name: 'mui',
          chunks: 'all',
          priority: 10,
        },
      },
    },
  },
};
