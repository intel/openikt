<template>
  <div class="account-management-component">
    <page-title></page-title>

    <div class="box">
      <div class="form-container log-in-container" id="log-in-container">
        <form>
          <h2 class="title">Login Account</h2>
          <input
            class="form-input"
            v-model.trim="logInForm.username"
            type="text"
            placeholder="Username"
            required />

          <div class="password-container">
            <input
              class="form-input"
              v-model.trim="logInForm.password"
              :type="logInShowPassword ? 'text' : 'password'"
              placeholder="Password"
              required />
            <i
              class="password-view-icon"
              :class="
                logInShowPassword
                  ? 'iconfont icon-mimabukejian'
                  : 'el-icon-view'
              "
              @click="logInShowPassword = !logInShowPassword"></i>
          </div>

          <a class="forget-password-link">Forget Password?</a>
          <button class="button" type="button" @click="handleLogIn">
            Log In
          </button>
        </form>
      </div>

      <div class="form-container sign-up-container" id="sign-up-container">
        <form>
          <h2 class="title">Create Account</h2>
          <input
            class="form-input"
            v-model.trim="signUpForm.username"
            type="text"
            placeholder="Username"
            required />

          <input
            class="form-input"
            v-model.trim="signUpForm.email"
            type="email"
            placeholder="Email"
            required />

          <div class="password-container">
            <input
              class="form-input"
              v-model.trim="signUpForm.password"
              :type="signUpShowPassword ? 'text' : 'password'"
              placeholder="Password"
              required />
            <i
              class="password-view-icon"
              :class="
                signUpShowPassword
                  ? 'iconfont icon-mimabukejian'
                  : 'el-icon-view'
              "
              @click="signUpShowPassword = !signUpShowPassword"></i>
          </div>
          <button class="button" type="button" @click="handleSignUp">
            Sign Up
          </button>
        </form>
      </div>

      <div class="switch-container" id="switch-container">
        <div class="switch-circle"></div>
        <div class="switch-circle switch-circle2"></div>

        <div class="switch-item is-hidden">
          <h2 class="title">Welcome Back！</h2>
          <p class="description">Already have an account? Log in!</p>
          <button class="button switch-btn">Log In</button>
        </div>

        <div class="switch-item">
          <h2 class="title">Hello Friend！</h2>
          <p class="description">register an account to join us.</p>
          <button class="button switch-btn">Sign Up</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import PageTitle from './components/PageTitle.vue'

import { logInAPI, signUpAPI } from '../../services/api/auth'

export default {
  name: 'AccountManagement',
  components: {
    PageTitle
  },
  data() {
    return {
      logInForm: {
        username: '',
        password: ''
      },
      signUpForm: {
        username: '',
        password: '',
        email: ''
      },
      logInShowPassword: false,
      signUpShowPassword: false
    }
  },
  methods: {
    async handleLogIn() {
      if (!this.logInForm.username || !this.logInForm.password) {
        return
      }

      const { code } = await logInAPI(
        this.logInForm.username,
        this.logInForm.password
      )
      if (code === 200) {
        this.$message({
          message: 'ok',
          type: 'success'
        })
      }
    },
    async handleSignUp() {
      if (
        !this.signUpForm.username ||
        !this.logInForm.password ||
        !this.signUpForm.email
      ) {
        return
      }

      const { code } = await signUpAPI(
        this.signUpForm.username,
        this.signUpForm.password,
        this.signUpForm.email
      )
      if (code === 200) {
        this.$message({
          message: 'ok',
          type: 'success'
        })
      }
    },
    switchAnimation() {
      const switchContainerEl = document.getElementById('switch-container')
      const switchItemsAllEl = document.querySelectorAll('.switch-item')
      const switchCirclesAllEl = document.querySelectorAll('.switch-circle')

      const formItemsAllEl = document.querySelectorAll('.form-container')

      const switchBtn = document.querySelectorAll('.switch-btn')

      const changeForm = () => {
        switchContainerEl.classList.add('is-gx')
        setTimeout(() => {
          switchContainerEl.classList.remove('is-gx')
        }, 1500)

        switchContainerEl.classList.toggle('is-txr')
        formItemsAllEl[1].classList.toggle('is-z')

        for (let i = 0; i < 2; i++) {
          switchItemsAllEl[i].classList.toggle('is-hidden')
          switchCirclesAllEl[i].classList.toggle('is-txr')
          formItemsAllEl[i].classList.toggle('is-txl')
        }
      }

      window.addEventListener('load', () => {
        for (let i = 0; i < switchBtn.length; i++) {
          switchBtn[i].addEventListener('click', changeForm)
        }
      })
    }
  },
  mounted() {
    this.switchAnimation()
  }
}
</script>

<style scoped>
.account-management-component {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  background-color: #ecf0f3;
}

.title {
  padding: 0;
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  line-height: 3;
  color: #181818;
}

.description {
  padding: 0;
  margin: 0;
  color: #a0a5a8;
  font-size: 14px;
  letter-spacing: 0.25px;
  text-align: center;
  line-height: 1.6;
}

.button {
  width: 180px;
  height: 50px;
  border-radius: 25px;
  margin-top: 50px;
  font-weight: 700;
  font-size: 14px;
  letter-spacing: 1.15px;
  background-color: #4b70e2;
  color: #f9f9f9;
  box-shadow: 8px 8px 16px #d1d9e6, -8px -8px 16px #f9f9f9;
  border: none;
  outline: none;
  box-sizing: border-box;
  cursor: pointer;
}

.button:hover {
  box-shadow: 6px 6px 10px #d1d9e6, -6px -6px 10px #f9f9f9;
  transform: scale(0.985);
  transition: all 0.25s;
}

.button:active,
.button:focus {
  box-shadow: 2px 2px 6px #d1d9e6, -2px -2px 6px #f9f9f9;
  transform: scale(0.97);
  transition: all 0.25s;
}

.box {
  position: relative;
  min-width: 1000px;
  min-height: 600px;
  padding: 25px;
  box-sizing: border-box;
  background-color: #ecf0f3;
  box-shadow: 10px 10px 10px #d1d9e6, -10px -10px 10px #f9f9f9;
  border-radius: 12px;
  overflow: hidden;
}

/* @media (max-width: 1200px) {
  .box {
    transform: scale(0.7);
  }
}

@media (max-width: 1000px) {
  .box {
    transform: scale(0.6);
  }
}

@media (max-width: 800px) {
  .box {
    transform: scale(0.5);
  }
}

@media (max-width: 600px) {
  .box {
    transform: scale(0.4);
  }
} */

.form-container {
  display: flex;
  justify-content: center;
  align-items: center;
  position: absolute;
  top: 0;
  width: 600px;
  height: 100%;
  padding: 25px;
  box-sizing: border-box;
  background-color: #ecf0f3;
  transition: all 1.25s;
}

form {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.password-container {
  position: relative;
}

.password-view-icon {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 18px;
  cursor: pointer;
  color: #6b7280;
}

.icon-mimabukejian {
  font-size: 22px;
}

.form-input {
  width: 350px;
  height: 40px;
  margin: 4px 0;
  padding-left: 25px;
  box-sizing: border-box;
  font-size: 14px;
  letter-spacing: 0.5px;
  border: none;
  outline: none;
  background-color: #ecf0f3;
  transition: all 0.25s ease;
  border-radius: 8px;
  box-shadow: 2px 2px 4px #d1d9e6 inset, -2px -2px 4px #f9f9f9 inset;
}

.form-input:focus {
  box-shadow: 4px 4px 4px #d1d9e6 inset, -4px -4px 4px #f9f9f9 inset;
}

.forget-password-link {
  color: #181818;
  font-size: 16px;
  margin-top: 25px;
  border-bottom: 1px solid #a0a5a8;
  line-height: 2;
}

.log-in-container {
  left: calc(100% - 600px);
  z-index: 100;
}

.sign-up-container {
  left: calc(100% - 600px);
  z-index: 0;
}

.switch-container {
  display: flex;
  justify-content: center;
  align-items: center;
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 400px;
  padding: 50px;
  z-index: 200;
  transition: all 1.25s;
  background-color: #ecf0f3;
  overflow: hidden;
  box-shadow: 4px 4px 10px #d1d9e6, -4px -4px 10px #d1d9e6;
  box-sizing: border-box;
}

.switch-circle {
  position: absolute;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  background-color: #ecf0f3;
  box-shadow: 8px 8px 12px #b8bec7 inset, -8px -8px 12px #fff inset;
  bottom: -60%;
  left: -60%;
  transition: all 1.25s;
}

.switch-circle2 {
  top: -30%;
  left: 60%;
  width: 300px;
  height: 300px;
}

.switch-item {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: absolute;
  width: 400px;
  padding: 50px 55px;
  box-sizing: border-box;
  transition: all 1.25s;
}

.is-txr {
  left: calc(100% - 400px);
  transition: all 1.25s;
  transform-origin: left;
}

.is-txl {
  left: 0;
  transition: all 1.25s;
  transform-origin: right;
}

.is-z {
  z-index: 200;
  transition: all 1.25s;
}

.is-hidden {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  transition: all 1.25s;
}

.is-gx {
  animation: is-gx 1.25s;
}

@keyframes is-gx {
  0%,
  10%,
  100% {
    width: 400px;
  }

  30%,
  50% {
    width: 500px;
  }
}
</style>
