<template>
  <div class="compare-item-component">
    <el-select
      v-model="imageName"
      :placeholder="isImport ? `Using Importing ${placeholder}` : placeholder"
      :disabled="isImport"
      size="small"
      clearable
      filterable
      style="width: 100%">
      <el-option
        v-for="item of imageList"
        :key="item.value"
        :value="item.label"></el-option>
    </el-select>

    <p v-if="isImport" class="import-tip">
      <el-popconfirm
        icon="el-icon-info"
        icon-color="red"
        title="Do you want to cancel import?"
        @confirm="cancelImport">
        <span slot="reference" class="cancel-import-text">
          Cancel import and use existing option.
        </span>
      </el-popconfirm>
    </p>
    <p v-else class="import-tip">
      <i
        class="iconfont icon-tishi"
        style="font-size: 18px; color: #f97316; margin-right: 5px"></i>
      <span style="color: #475569">
        No suitable option
        <i
          class="iconfont icon-wenhao"
          style="font-size: 16px; font-weight: 700"></i>
      </span>
      &nbsp;
      <span class="import-text" @click="importImage">
        I want to import it myself.
        <i class="iconfont icon-daoru" style="font-size: 18px"></i>
      </span>
    </p>

    <el-card class="import-card" v-if="isImport" shadow="always">
      <h3 class="import-title">{{ `Import ${placeholder}` }}</h3>

      <el-form ref="form" :model="form" :rules="rules" size="mini">
        <el-form-item label="OS" prop="os">
          <el-select v-model="form.os" style="width: 100%">
            <el-option
              v-for="item of osList"
              :key="item.value"
              :label="item.label"
              :value="item.value"></el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="Name" prop="name">
          <el-input v-model="form.name" clearable></el-input>
        </el-form-item>

        <el-form-item label="Release" prop="release">
          <el-input v-model="form.release" clearable></el-input>
        </el-form-item>

        <el-form-item>
          <el-radio v-model="type" label="url">URL</el-radio>
          <el-radio v-model="type" label="rawData">Raw Data</el-radio>
        </el-form-item>

        <el-form-item v-if="type === 'url'" prop="url" key="url">
          <el-input v-model="form.url" clearable></el-input>
        </el-form-item>

        <el-form-item v-else prop="rawData" key="rawData">
          <el-upload
            :data="{ imageName: form.name }"
            action="/v1/openikt/app_ii/raw_data_upload"
            :limit="1"
            :on-success="uploadSuccess">
            <el-button
              :disabled="!form.name || !isNameUnique"
              size="mini"
              type="primary">
              click upload
            </el-button>
          </el-upload>
        </el-form-item>

        <el-form-item label="Description" prop="desc">
          <el-input type="textarea" v-model="form.desc" clearable></el-input>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import {
  verifyCreateImageNameAPI,
  verifyCreateImageUrlAPI
} from '@/services/api/image-comparison'

export default {
  name: 'CompareItem',
  props: {
    imageList: {
      type: Array,
      default: () => []
    },
    osList: {
      type: Array,
      default: () => []
    },
    placeholder: {
      type: String,
      default: 'Image'
    }
  },
  data() {
    return {
      isImport: false,
      isNameUnique: false,
      type: 'url',
      imageName: '',
      form: {
        os: '',
        name: '',
        release: '',
        desc: '',
        url: '',
        rawData: ''
      },
      rules: {
        os: [
          { required: true, message: 'please select os', trigger: 'change' }
        ],
        name: [
          { required: true, message: 'please enter name', trigger: 'blur' },
          {
            validator: async (rule, value, callback) => {
              if (!value) return

              this.isNameUnique = await verifyCreateImageNameAPI(value)

              if (this.isNameUnique) {
                callback()
              } else {
                callback(new Error('The name already exists, please re-enter.'))
              }
            }
          }
        ],
        release: [
          { required: true, message: 'please enter release', trigger: 'blur' }
        ],
        url: [{ required: true, message: 'please enter url', trigger: 'blur' }],
        rawData: [
          { required: true, message: 'please upload file', trigger: 'change' }
        ]
      }
    }
  },
  methods: {
    async checkAndReturnImageData() {
      const imageData = {
        isImport: this.isImport
      }

      if (!this.isImport) {
        if (!this.imageName) {
          this.$message.warning(`Please select ${this.placeholder}`)
          return false
        } else {
          imageData.value = this.imageName
          return imageData
        }
      } else {
        try {
          await this.$refs.form?.validate()

          if (this.type === 'url') {
            const { valid } = await verifyCreateImageUrlAPI(this.form.url)

            if (!valid) {
              throw Error(
                `URL (${this.form.url}) is not a valid link, please fill it in again.`
              )
            }
          }

          const value = {
            ...this.form
          }
          delete value[this.type === 'url' ? 'rawData' : 'url']
          imageData.value = value
          return imageData
        } catch (e) {
          const errorMessage = e.message
          if (errorMessage) {
            this.$message.error(errorMessage)
          } else {
            this.$message.warning(
              `Please check the "Import ${this.placeholder}" form`
            )
          }
        }
      }
    },
    uploadSuccess() {
      this.form.rawData = this.form.name
    },
    importImage() {
      this.isImport = true
      this.imageName = ''
    },
    cancelImport() {
      this.isImport = false
      this.form = {
        os: '',
        name: '',
        release: '',
        desc: '',
        url: '',
        rawData: ''
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.import-tip {
  text-align: center;
  font-size: 14px;

  .import-text {
    color: #3b82f6;
    cursor: pointer;

    &:hover {
      text-decoration: underline;
    }
  }
}

.cancel-import-text {
  color: #818cf8;
  cursor: pointer;

  &:hover {
    text-decoration: underline;
  }
}

.import-card {
  border-radius: 20px;

  .import-title {
    margin-top: 0;
    text-align: center;
  }
}
</style>
