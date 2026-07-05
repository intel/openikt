import Vue from 'vue'
import VueRouter from 'vue-router'
import Cookies from 'js-cookie'

import BasicLayout from '@/components/layouts'

Vue.use(VueRouter)

const routes = [
  {
    path: '/welcome',
    name: 'welcome',
    meta: {
      // Login / register page must be reachable without authentication.
      public: true
    },
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

  // Auth guard: every route except those flagged `meta.public` requires a
  // logged-in user. The backend enforces IsAuthenticated globally, so
  // redirect anonymous users to the login page instead of letting the page
  // load and fire API calls that would only return 403.
  const isPublic = to.matched.some((record) => record.meta && record.meta.public)
  const isLoggedIn = !!Cookies.get('username')

  if (!isPublic && !isLoggedIn) {
    next({ name: 'welcome' })
  } else if (isPublic && isLoggedIn && to.name === 'welcome') {
    // Already authenticated users have no reason to see the login page.
    next({ path: '/' })
  } else {
    next()
  }
})

export default router
