<template>
  <div class="home">
    <el-carousel :interval="5000" arrow="always">
      <el-carousel-item @click.native="handleClickBanner('/openikt/')">
        <div class="xdd xdd1"></div>
      </el-carousel-item>

      <el-carousel-item @click.native="handleClickBanner('/openikt/quiltdiff')">
        <div class="xdd xdd2"></div>
      </el-carousel-item>

      <el-carousel-item @click.native="handleClickBanner('/openikt/help')">
        <div class="xdd xdd3"></div>
      </el-carousel-item>
    </el-carousel>

    <div class="our-services">
      <h3 class="title">Our Services</h3>
      <div class="quilt-diff">
        <img src="" alt="" />
        <p class="quilt-diff-title">Quilt Diff</p>
        <p class="quilt-diff-des">
          Quilt Diff simplifies understanding and reviewing changes by
          visualizing version differences and upstream information on a web
          page, eliminating the need for in-depth knowledge of git commands.
        </p>
      </div>
    </div>

    <footer>Copyright © 2024 , OpenIKT team</footer>
  </div>
</template>

<script>
export default {
  methods: {
    handleClickBanner(url) {
      window.open(url, '_blank')
    }
  }
}
</script>

<style lang="scss" scoped>
.home {
  width: 100%;
  padding-bottom: 10px;
  box-sizing: border-box;
  min-height: calc(100vh - 60px);
  background: url(../assets/images/bg-services.svg) 0px 200px/100% no-repeat,
    linear-gradient(#5b58f4, #270794);

  ::v-deep .el-carousel {
    height: 400px;
    cursor: pointer;

    .el-carousel__container {
      height: 400px;
    }
  }

  .xdd {
    width: 100%;
    height: 100%;
  }

  .xdd1 {
    background: url(../assets/images/banner1.png) no-repeat;
    background-size: 100% 100%;
  }
  .xdd2 {
    background: url(../assets/images/banner2.png) no-repeat;
    background-size: 100% 100%;
  }
  .xdd3 {
    background: url(../assets/images/banner3.png) no-repeat;
    background-size: 100% 100%;
  }

  .our-services {
    margin-top: 20px;

    .title {
      font-size: 28px;
      color: #fff;
      text-align: center;
      margin-top: 0;
    }

    .quilt-diff {
      width: 400px;
      height: 200px;
      background-image: linear-gradient(
        65.9deg,
        rgba(85, 228, 224, 1) 5.5%,
        rgba(75, 68, 224, 0.74) 54.2%,
        rgba(64, 198, 238, 1) 55.2%,
        rgba(177, 36, 224, 1) 98.4%
      );
      margin: 0 auto;
      border-radius: 10px;
      padding: 10px;
      box-sizing: border-box;

      color: #fff;

      .quilt-diff-title {
        font-size: 22px;
        text-align: center;
        font-weight: 700;
      }

      .quilt-diff-des {
        text-indent: 2em;
        color: #f8fafc;
        font-weight: 700;
        word-break: break-all;
      }
    }
  }

  footer {
    margin-top: 100px;
    color: #fff;
    text-align: center;
  }
}
</style>
