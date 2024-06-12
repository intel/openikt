<template>
  <div class="help-container">
    <el-card>
      <h2>
        Contact US
        <i
          class="iconfont icon-tuandui"
          style="color: #22d3ee; font-size: 30px"></i>
        OpenIKT Team
      </h2>

      <a class="link" href="mailto:ikt_devops@intel.com" title="email">
        <i
          class="iconfont icon-dianziyouxiang"
          style="color: #2563eb; font-size: 26px"></i>
        ikt_devops@intel.com
      </a>

      <a
        class="link"
        href="https://github.com/intel/openikt/wiki"
        target="_blank"
        title="wiki">
        <i
          class="iconfont icon-wiki"
          style="color: #22c55e; font-size: 20px"></i>
        https://github.com/intel/openikt/wiki
      </a>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'Help'
}
</script>

<style lang="scss">
.help-container {
  margin-top: 120px;
  display: flex;
  align-items: center;
  justify-content: center;

  .el-card__body {
    width: 500px;
    height: 200px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;

    .link {
      color: #334155;

      &:hover {
        color: #2563eb;
      }
    }
  }
}
</style>
