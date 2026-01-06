<template>
  <el-dialog
    class="create-quilt-diff-component"
    title="Create Quilt Diff"
    :visible="dialogVisible"
    :close-on-click-modal="false"
    @close="closeDialog">
    <el-form
      ref="form"
      :model="form"
      :rules="rules"
      label-width="100px"
      size="small">
      <el-form-item label="Diff Type" prop="diffType">
        <el-select
          v-model="form.diffType"
          placeholder="The type of algorithms for generating diff"
          style="width: 100%">
          <el-option
            v-for="item of diffTypeList"
            :key="item.label"
            :value="item.label"></el-option>
        </el-select>
      </el-form-item>

      <fieldset>
        <legend>From</legend>
        <el-form-item label="Repository" prop="repositoryFrom">
          <el-input
            v-model="form.repositoryFrom"
            placeholder="Repository url of the start ref"
            clearable></el-input>
        </el-form-item>

        <el-form-item label="Ref" prop="refFrom">
          <el-input
            v-model="form.refFrom"
            placeholder="Ref of the start git range, could be tag, branch or sha1"
            clearable></el-input>
        </el-form-item>

        <el-form-item label="Base">
          <el-input
            v-model="form.baseFrom"
            placeholder="Base of the start git range, could be tag, branch or sha1"
            clearable></el-input>
        </el-form-item>
      </fieldset>

      <fieldset>
        <legend>To</legend>
        <el-form-item label="Repository" prop="repositoryTo">
          <el-input
            v-model="form.repositoryTo"
            placeholder="Repository url of the end ref"
            clearable></el-input>
        </el-form-item>

        <el-form-item label="Ref" prop="refTo">
          <el-input
            v-model="form.refTo"
            placeholder="Ref of the end git range, could be tag, branch or sha1"
            clearable></el-input>
        </el-form-item>

        <el-form-item label="Base">
          <el-input
            v-model="form.baseTo"
            placeholder="Base of the end start git range, could be tag, branch or sha1"
            clearable></el-input>
        </el-form-item>
      </fieldset>
    </el-form>

    <div class="footer" slot="footer">
      <el-button size="small" @click="closeDialog">Cancel</el-button>
      <el-button size="small" type="primary" @click="createQuiltDiff">
        Create
      </el-button>
    </div>
  </el-dialog>
</template>

<script>
import {
  getQuiltDiffTypeAPI,
  createQuiltDiffAPI
} from '@/services/api/quilt-diff'

export default {
  name: 'CreateQuiltDiff',
  props: {
    dialogVisible: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      form: {
        diffType: '',
        repositoryFrom: '',
        refFrom: '',
        baseFrom: '',
        repositoryTo: '',
        refTo: '',
        baseTo: ''
      },
      rules: {
        diffType: [
          {
            required: true,
            message: 'please select diff type',
            trigger: 'change'
          }
        ],
        repositoryFrom: [
          {
            required: true,
            message: 'please enter Repository From',
            trigger: 'blur'
          }
        ],
        refFrom: [
          {
            required: true,
            message: 'please enter ref from',
            trigger: 'blur'
          }
        ],
        repositoryTo: [
          {
            required: true,
            message: 'please enter repository to',
            trigger: 'blur'
          }
        ],
        refTo: [
          {
            required: true,
            message: 'please enter ref to',
            trigger: 'blur'
          }
        ]
      },
      diffTypeList: []
    }
  },
  methods: {
    createQuiltDiff() {
      this.$refs.form?.validate(async isValid => {
        if (!isValid) return

        const { code } = await createQuiltDiffAPI(this.form)
        if (code === 0) {
          this.$message.success(
            'Task created successfully, which will take about 1 hour to complete.'
          )
          this.closeDialog()
        }
      })
    },
    closeDialog() {
      this.$refs.form?.resetFields()
      this.$emit('update:dialog-visible', false)
    },
    async getQuiltDiffType() {
      ;({ data: this.diffTypeList } = await getQuiltDiffTypeAPI())
    }
  },
  created() {
    this.getQuiltDiffType()
  }
}
</script>

<style lang="scss" scoped>
.create-quilt-diff-component {
  fieldset {
    border-color: #f1f5f9;
  }

  .footer {
    text-align: center;
  }
}
</style>
