plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "dev.appi.runtime"
    compileSdk = 35

    defaultConfig {
        applicationId = "dev.appi.runtime"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0-placeholder"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildTypes {
        release {
            isMinifyEnabled = false
        }
        debug {
            applicationIdSuffix = ".debug"
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
}
