export function extractNameInitials(fullName) {
  const names = fullName.split(' ')
  const firstName = names[0].charAt().toUpperCase()
  const lastName = names[1]?.charAt()?.toUpperCase() || ''
  return firstName + lastName
}

export function downloadExcelFile(data, filename) {
  const link = document.createElement('a')
  const blod = new Blob([data], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  })
  const blodUrl = window.URL.createObjectURL(blod)
  link.href = blodUrl
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(blodUrl)
}
