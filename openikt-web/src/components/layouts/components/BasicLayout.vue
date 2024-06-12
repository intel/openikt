<template>
  <el-container class="basic-layout-component">
    <el-header
      class="layout-header"
      :style="{ height: isInHomePage ? '60px' : '40px' }">
      <ikt-navigation></ikt-navigation>
    </el-header>

    <el-main class="layout-main" :class="{ 'is-home': isInHomePage }">
      <router-view></router-view>
    </el-main>
  </el-container>
</template>

<script>
import IktNavigation from '@/components/navigation'

export default {
  name: 'BasicLayout',
  components: {
    IktNavigation
  },
  computed: {
    isInHomePage() {
      return this.$route.path === '/'
    }
  }
}
</script>

<style lang="scss" scoped>
.basic-layout-component {
  width: 100%;
  height: 100%;

  .layout-header {
    padding: 0;
  }

  .layout-main {
    width: 100%;

    padding: 0;
    box-sizing: border-box;
    overflow: auto;
    background-color: #f8fafc;

    &.is-home {
      height: calc(100% - 60px);
    }
  }
}
</style>
