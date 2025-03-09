/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_EVENTHUB_CONNECTION_STRING: string
  readonly VITE_CONSUMER_GROUP: string
  readonly VITE_DEVICE_ID: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
