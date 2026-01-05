import { toast } from 'react-hot-toast'

export const notify = {
  success: (msg, opts) => toast.success(msg, opts),
  error: (msg, opts) => toast.error(msg, opts),
  info: (msg, opts) => toast(msg, opts),
  promise: (p, { loading = 'Working…', success = 'Done!', error = 'Failed' } = {}) =>
    toast.promise(p, { loading, success, error }),
}
