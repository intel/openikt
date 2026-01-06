import iktRequest from '../..'

export function signUpAPI(username, password, email) {
  return iktRequest.post({
    url: '/openikt/auth/sign-up',
    data: {
      username,
      password,
      email
    }
  })
}

export function logInAPI(username, password) {
  return iktRequest.post({
    url: '/openikt/auth/login',
    data: {
      username,
      password
    }
  })
}

export function logoutAPI() {
  return iktRequest.get({
    url: '/openikt/auth/logout/'
  })
}
