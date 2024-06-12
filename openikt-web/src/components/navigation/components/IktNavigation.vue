<template>
  <div class="ikt-navigation-component" :class="{ 'is-home': isInHomePage }">
    <div class="left-area">
      <h1 class="logo-container">
        <router-link to="/" class="logo-link">
          <img alt="logo" src="@/assets/images/intel-header-logo.svg" />
        </router-link>

        <div class="logo-text">OpenIKT</div>
      </h1>

      <el-menu
        :default-active="defaultActiveIndex"
        mode="horizontal"
        background-color="#1d4ed8"
        text-color="#fff"
        active-text-color="#ffd04b">
        <el-menu-item index="/quiltdiff">
          <router-link to="/quiltdiff">Quilt Diff</router-link>
        </el-menu-item>

        <el-menu-item index="/help">
          <router-link to="/help">Help</router-link>
        </el-menu-item>
      </el-menu>
    </div>

    <div class="right-area"></div>
  </div>
</template>

<script>
export default {
  name: 'IktNavigation',
  computed: {
    defaultActiveIndex() {
      const { path, meta } = this.$route
      const menuIndex = meta.menuIndex
      return menuIndex ? menuIndex : path
    },
    isInHomePage() {
      return this.$route.path === '/'
    }
  }
}
</script>

<style lang="scss" scoped>
a {
  display: block;
  box-sizing: border-box;
  color: #fff;
}

.el-menu--horizontal {
  .el-menu-item {
    padding: 0 !important;

    &.is-active a {
      color: #ffd04b;
    }

    a {
      padding: 0 10px;
    }
  }
}

.ikt-navigation-component {
  display: flex;
  height: 100%;
  padding: 0 20px;
  justify-content: space-between;
  background-color: #1d4ed8;
  overflow: hidden;

  &.is-home {
    height: 60px;
    background-image: linear-gradient(#5b58f4, #270794) !important;

    .logo-container {
      width: 200px !important;

      .logo-link img {
        width: 50px !important;
        margin-right: 5px;
      }

      .logo-text {
        font-size: 22px;
      }
    }

    .el-menu-item {
      line-height: 60px !important;
      border-bottom: none;
      font-size: 16px;
      background-image: linear-gradient(#5b58f4, #270794) !important;
    }
  }

  .left-area {
    display: flex;

    .logo-container {
      width: 100px;
      margin: 0;
      display: flex;
      justify-content: center;
      align-items: center;
      font-size: 14px;
      color: #fff;

      .logo-link img {
        width: 30px;
        margin-right: 5px;
      }
    }

    ::v-deep .el-menu {
      border: none;

      .el-menu-item {
        padding: 0;
        line-height: 40px;
      }

      .el-submenu .el-submenu__title,
      a {
        padding: 0 10px;
      }
    }
  }
}
</style>
