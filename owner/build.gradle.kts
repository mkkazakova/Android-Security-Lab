plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}
android {
    namespace = "org.example.securitylab.owner"
    compileSdk = 36
    defaultConfig {
        applicationId = "org.example.securitylab.owner"
        minSdk = 26
        targetSdk = 33
        versionCode = 1
        versionName = "0.1-stage1"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}
