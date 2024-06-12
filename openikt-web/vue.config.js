module.exports = {
  publicPath: '/openikt/',
  lintOnSave: true,
  devServer: {
    host: '0.0.0.0',
    open: true,
    compress: true,
    disableHostCheck: true,
    port: 7777,
    proxy: {
      '/v1': {
        target: process.env.VUE_APP_DEV_SERVER_PROXY_URL,
        pathRewrite: {
          '^/v1': ''
        },
        changeOrigin: true
      }
    }
  }
}
