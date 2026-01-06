import Vue from 'vue'
import VueRouter from 'vue-router'

import BasicLayout from '@/components/layouts'

Vue.use(VueRouter)

const routes = [
  {
    path: '/welcome',
    name: 'welcome',
    component: () => import('../views/account-management/AccountManagement.vue')
  },
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
        component: () => import('../views/quilt-diff/QuiltDiff.vue'),
        meta: {
          title: 'Quilt Diff'
        }
      },
      {
        path: 'quiltdiff/details/:id',
        name: 'quiltDiffDetails',
        component: () =>
          import('../views/quilt-diff/components/QuiltDiffDetails.vue'),
        meta: {
          title: 'Details-Quilt Diff',
          menuIndex: '/quiltdiff'
        }
      },
      {
        path: 'image-comparison',
        name: 'imageComparison',
        component: () => import('../views/image-comparison/ComparisonList.vue'),
        meta: {
          title: 'Image Comparison'
        }
      },
      {
        path: 'image-comparison/create',
        name: 'imageComparisonCreate',
        component: () =>
          import('../views/image-comparison/CreateComparison.vue'),
        meta: {
          title: 'Create Image Comparison',
          menuIndex: '/image-comparison'
        }
      },
      {
        path: 'image-comparison/details/:id',
        name: 'imageComparisonDetails',
        component: () =>
          import('../views/image-comparison/ComparisonDetails.vue'),
        meta: {
          title: 'Details-Image Comparison',
          menuIndex: '/image-comparison'
        }
      },
      {
        path: 'help',
        name: 'help',
        component: () => import('../views/help/Help.vue'),
        meta: {
          title: 'Help'
        }
      }
    ]
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

router.beforeEach((to, from, next) => {
  const title = to.meta.title
  document.title = title ? title : 'OpenIKT'
  next()
})

export default router
