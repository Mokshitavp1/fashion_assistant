import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('axios', () => {
    const state = {
        requestHandlers: [],
        responseErrorHandlers: [],
        responseSuccessHandlers: [],
        apiInstance: null,
    }

    const reset = () => {
        state.requestHandlers = []
        state.responseErrorHandlers = []
        state.responseSuccessHandlers = []

        const apiFn = vi.fn((requestConfig) => Promise.resolve({ data: { retried: true }, config: requestConfig }))
        apiFn.get = vi.fn()
        apiFn.post = vi.fn()
        apiFn.delete = vi.fn()
        apiFn.interceptors = {
            request: {
                use: vi.fn((handler) => {
                    state.requestHandlers.push(handler)
                    return state.requestHandlers.length - 1
                }),
            },
            response: {
                use: vi.fn((successHandler, errorHandler) => {
                    state.responseSuccessHandlers.push(successHandler)
                    state.responseErrorHandlers.push(errorHandler)
                    return state.responseErrorHandlers.length - 1
                }),
            },
        }

        state.apiInstance = apiFn
    }

    reset()

    const axiosDefault = {
        create: vi.fn(() => state.apiInstance),
        post: vi.fn(),
        __state: state,
        __reset: reset,
    }

    return { default: axiosDefault }
})

const loadModule = async () => {
    vi.resetModules()
    const axiosModule = await import('axios')
    axiosModule.default.__reset()
    const apiModule = await import('./api')
    return {
        apiModule,
        axiosMock: axiosModule.default,
        apiMock: axiosModule.default.__state.apiInstance,
    }
}

describe('frontend api service', () => {
    beforeEach(() => {
        localStorage.clear()
        vi.clearAllMocks()
    })

    it('returns register response without storing auth tokens', async () => {
        const { apiModule, apiMock } = await loadModule()
        const payload = { email_verification_required: true, email: 'alice@example.com' }
        apiMock.post.mockResolvedValueOnce({ data: payload })

        const response = await apiModule.createUser('Alice', 'alice@example.com', 'Secret123A')

        expect(apiMock.post).toHaveBeenCalledWith('/auth/register', {
            name: 'Alice',
            email: 'alice@example.com',
            password: 'Secret123A',
        })
        expect(response.data.email_verification_required).toBe(true)
        expect(localStorage.getItem('accessToken')).toBeNull()
        expect(localStorage.getItem('refreshToken')).toBeNull()
        expect(localStorage.getItem('userId')).toBeNull()
    })

    it('logs out and clears local storage', async () => {
        const { apiModule, apiMock } = await loadModule()
        localStorage.setItem('refreshToken', 'r-token')
        localStorage.setItem('accessToken', 'a-token')
        localStorage.setItem('userId', '9')
        apiMock.post.mockResolvedValueOnce({ data: { detail: 'ok' } })

        await apiModule.logoutUser()

        expect(apiMock.post).toHaveBeenCalledWith('/auth/logout', { refresh_token: 'r-token' })
        expect(localStorage.getItem('refreshToken')).toBeNull()
        expect(localStorage.getItem('accessToken')).toBeNull()
        expect(localStorage.getItem('userId')).toBeNull()
    })

    it('sends FormData payload for analyzeUser', async () => {
        const { apiModule, apiMock } = await loadModule()
        apiMock.post.mockResolvedValueOnce({ data: { queued: true } })
        const blob = new Blob(['img'], { type: 'image/jpeg' })

        await apiModule.analyzeUser(11, blob, 170, 65)

        const [url, formData] = apiMock.post.mock.calls[0]
        expect(url).toBe('/users/11/analyze')
        expect(formData instanceof FormData).toBe(true)
        expect(formData.get('height')).toBe('170')
        expect(formData.get('weight')).toBe('65')
    })

    it('retries once on 401 by refreshing token', async () => {
        const { axiosMock, apiMock } = await loadModule()
        localStorage.setItem('refreshToken', 'refresh-old')
        localStorage.setItem('accessToken', 'access-old')

        axiosMock.post.mockResolvedValueOnce({
            data: { access_token: 'access-new', refresh_token: 'refresh-new', user_id: 5 },
        })

        const originalRequest = { url: '/users/5/wardrobe', headers: {} }
        const interceptorError = {
            response: { status: 401 },
            config: originalRequest,
        }

        const result = await axiosMock.__state.responseErrorHandlers[0](interceptorError)

        expect(axiosMock.post).toHaveBeenCalledWith('http://127.0.0.1:8000/auth/refresh', {
            refresh_token: 'refresh-old',
        })
        expect(originalRequest._retry).toBe(true)
        expect(originalRequest.headers.Authorization).toBe('Bearer access-new')
        expect(localStorage.getItem('accessToken')).toBe('access-new')
        expect(localStorage.getItem('refreshToken')).toBe('refresh-new')
        expect(result.data.retried).toBe(true)
        expect(apiMock).toHaveBeenCalledTimes(1)
    })

    it('clears tokens if refresh fails', async () => {
        const { axiosMock } = await loadModule()
        localStorage.setItem('refreshToken', 'refresh-old')
        localStorage.setItem('accessToken', 'access-old')
        localStorage.setItem('userId', '3')

        axiosMock.post.mockRejectedValueOnce(new Error('refresh failed'))

        const originalRequest = { url: '/users/3', headers: {} }
        const interceptorError = {
            response: { status: 401 },
            config: originalRequest,
        }

        await expect(axiosMock.__state.responseErrorHandlers[0](interceptorError)).rejects.toThrow('refresh failed')

        expect(localStorage.getItem('refreshToken')).toBeNull()
        expect(localStorage.getItem('accessToken')).toBeNull()
        expect(localStorage.getItem('userId')).toBeNull()
    })
})
