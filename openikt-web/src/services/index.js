import IKTRequest from './request'
import Cookies from 'js-cookie'

const iktRequest = new IKTRequest({
  baseURL: process.env.VUE_APP_AJAX_URL,
  timeout: 60000,
  interceptors: {
    requestInterceptor(config) {
      const csrfToken = Cookies.get('csrftoken')
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken
      }
      return config
    }
  }
})

export default iktRequest
