const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  devServer: {
    historyApiFallback: true,
    proxy: {
      '/': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  },
  transpileDependencies: true
})
