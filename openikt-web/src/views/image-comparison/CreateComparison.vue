<template>
  <div class="create-image-comparison-component">
    <h2 class="title">Create Image Comparison</h2>

    <el-row>
      <el-col :span="10">
        <compare-item
          ref="imgA"
          placeholder="Image A"
          :image-list="imageList"
          :os-list="osList"></compare-item>
      </el-col>

      <el-col class="vs-icon-container" :span="1">
        <i
          class="iconfont icon-bijiao"
          style="font-size: 22px; color: #ff5959"></i>
      </el-col>

      <el-col :span="10">
        <compare-item
          ref="imgB"
          placeholder="Image B"
          :image-list="imageList"
          :os-list="osList"></compare-item>
      </el-col>

      <el-col :span="3" style="padding-left: 20px">
        <el-button type="primary" size="small" @click="createImageComparison">
          Compare
        </el-button>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import CompareItem from './components/CompareItem.vue'
import {
  getImageListAPI,
  getOSListAPI,
  createImageComparisonAPI,
  verifyCreateImageExistAPI
} from '@/services/api/image-comparison'

export default {
  name: 'CreateImageComparison',
  components: {
    CompareItem
  },
  data() {
    return {
      imageList: [],
      osList: []
    }
  },
  methods: {
    async createImageComparison() {
      const imgA = await this.$refs.imgA?.checkAndReturnImageData()
      const imgB = await this.$refs.imgB?.checkAndReturnImageData()

      if (imgA && imgB) {
        const imgAName = imgA.isImport ? imgA.value.name : imgA.value
        const imgBName = imgB.isImport ? imgB.value.name : imgB.value

        const { is_exist, id } = await verifyCreateImageExistAPI(
          imgAName,
          imgBName
        )

        if (is_exist) {
          this.$confirm('image comparison already exists', 'Tip', {
            confirmButtonText: 'View',
            cancelButtonText: 'Cancel',
            type: 'warning'
          })
            .then(() => {
              this.$router.push(`/image-comparison?id=${id}`)
            })
            .catch(() => {
              this.$message({
                type: 'info',
                message: 'Cancelled'
              })
            })
          return
        }

        const { code } = await createImageComparisonAPI({ imgA, imgB })

        if (code === 0) {
          if (imgA.isImport || imgB.isImport) {
            this.$message.success({
              customClass: 'success-tip',
              type: 'success',
              duration: 0,
              offset: 300,
              showClose: true,
              onClose: () => {
                this.$router.push('/image-comparison')
              },
              message:
                'Successfully, the task creation is triggered. Due to the existence of the "import image" task, it is time-consuming. Please visit the main "Image Comparison" page again after some time.'
            })
          } else {
            this.$message.success(
              'Successfully, the task creation is triggered.'
            )
            this.$router.push('/image-comparison')
          }
        }
      }
    },
    async getImageList() {
      ;({ data: this.imageList } = await getImageListAPI())
    },
    async getOSList() {
      ;({ data: this.osList } = await getOSListAPI())
    }
  },
  created() {
    this.getImageList()
    this.getOSList()
  }
}
</script>

<style lang="scss" scoped>
.create-image-comparison-component {
  padding: 10px 20px;

  .vs-icon-container {
    height: 32px;
    display: flex;
    justify-content: center;
    align-items: center;
  }
}
</style>

<style>
.success-tip .el-message__content {
  font-size: 18px;
}
</style>
