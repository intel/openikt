import Vue from 'vue'
import VueRouter from 'vue-router'

import BasicLayout from '@/components/layouts'

Vue.use(VueRouter)

const routes = [
  // {
  //   path: '/welcome',
  //   name: 'welcome',
  //   component: () => import('../views/account-management/AccountManagement.vue')
  // },
  {
    path: '',
    // redirect: '/quiltdiff',
    component: BasicLayout,
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('../views/Home.vue')
      },
      {
        path: 'quiltdiff',
        name: 'quiltDiff',
        component: () => import('../views/quilt-diff/QuiltDiff.vue')
      },
      {
        path: 'quiltdiff/details/:id',
        name: 'quiltDiffDetails',
        component: () =>
          import('../views/quilt-diff/components/QuiltDiffDetails.vue'),
        meta: {
          menuIndex: '/quiltdiff'
        }
      },
      {
        path: 'help',
        name: 'help',
        component: () => import('../views/help/Help.vue')
      }
    ]
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router
