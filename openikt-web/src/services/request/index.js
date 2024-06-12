import axios from 'axios'
import router from '@/router'
import { Message } from 'element-ui'

class IKTRequest {
  constructor(config) {
    this.instance = axios.create(config)
    this.interceptors = config.interceptors
    this.instance.interceptors.request.use(
      config => {
        return config
      },
      error => {
        console.error(
          'Errors caught by request interceptors that are common globally to all Axios instances'
        )
        console.dir(error)
      }
    )

    this.instance.interceptors.response.use(
      res => {
        return res
      },
      error => {
        console.error(
          'Errors caught by response interceptors that are common globally to all Axios instances'
        )
        Message.error(
          error.response?.data?.msg ??
            error.response?.data?.detail ??
            error.message
        )
        console.dir(error)
        switch (error.response.status) {
          case 404:
            router.replace('/not-found')
            break
        }
        return Promise.reject(error)
      }
    )

    this.instance.interceptors.request.use(
      this.interceptors?.requestInterceptor,
      this.interceptors?.requestInterceptorCatch
    )

    this.instance.interceptors.response.use(
      this.interceptors?.responseInterceptor,
      this.interceptors?.responseInterceptorCatch
    )
  }

  request(config) {
    if (config.interceptors?.requestInterceptor) {
      config = config.interceptors.requestInterceptor(config)
    }

    return new Promise((resolve, reject) => {
      this.instance
        .request(config)
        .then(res => {
          if (config.interceptors?.responseInterceptor) {
            res = config.interceptors.responseInterceptor(res)
          }

          resolve(res.data)
        })
        .catch(err => {
          reject(err)
          return err
        })
    })
  }

  get(config) {
    return this.request({ ...config, method: 'GET' })
  }

  post(config) {
    return this.request({ ...config, method: 'POST' })
  }

  delete(config) {
    return this.request({ ...config, method: 'DELETE' })
  }

  patch(config) {
    return this.request({ ...config, method: 'PATCH' })
  }

  put(config) {
    return this.request({ ...config, method: 'PUT' })
  }
}

export default IKTRequest
