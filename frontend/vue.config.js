const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  devServer: {
    proxy: {
      '/': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  },
  transpileDependencies: true
})
