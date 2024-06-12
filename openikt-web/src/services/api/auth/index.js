import iktRequest from '../..'

export function signUpAPI(username, password, email) {
  return iktRequest.post({
    url: '/auth/sign-up',
    data: {
      username,
      password,
      email
    }
  })
}

export function logInAPI(username, password) {
  return iktRequest.post({
    url: '/auth/login',
    data: {
      username,
      password
    }
  })
}
