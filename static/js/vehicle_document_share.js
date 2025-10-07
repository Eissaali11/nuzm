/**
 * نصوص JavaScript لمشاركة وثائق السيارة عبر الواتساب مع الملفات
 */

async function shareVehicleDocuments() {
    try {
        // الحصول على معلومات السيارة من الصفحة
        const plateNumber = document.querySelector('[data-plate-number]')?.dataset.plateNumber || '';
        const make = document.querySelector('[data-make]')?.dataset.make || '';
        const model = document.querySelector('[data-model]')?.dataset.model || '';
        const year = document.querySelector('[data-year]')?.dataset.year || '';
        
        // معلومات السائق الحالي
        const currentDriver = document.querySelector('[data-current-driver]')?.dataset.currentDriver || 'غير محدد';
        const driverPhone = document.querySelector('[data-driver-phone]')?.dataset.driverPhone || '';
        
        // الروابط للوثائق
        const registrationFormLink = document.querySelector('[data-registration-form]')?.dataset.registrationForm || null;
        const insuranceFileLink = document.querySelector('[data-insurance-file]')?.dataset.insuranceFile || null;
        
        // إعداد رسالة مفصلة منظمة
        let message = `🚗 *تفاصيل مركبة - نُظم*\n\n`;
        message += `━━━━━━━━━━━━━━━━━━━━━━\n\n`;
        
        // معلومات المركبة
        message += `📋 *معلومات المركبة:*\n`;
        message += `🔹 رقم اللوحة: ${plateNumber}\n`;
        if (make) message += `🔹 الماركة: ${make}\n`;
        if (model) message += `🔹 الموديل: ${model}\n`;
        if (year) message += `🔹 السنة: ${year}\n`;
        message += `\n`;
        
        // معلومات السائق الحالي
        if (currentDriver && currentDriver !== 'غير محدد') {
            message += `👨‍💼 *السائق الحالي:*\n`;
            message += `🔹 الاسم: ${currentDriver}\n`;
            if (driverPhone) {
                message += `🔹 الهاتف: ${driverPhone}\n`;
            }
            message += `\n`;
        }
        
        // قسم الوثائق
        const documentsCount = (registrationFormLink ? 1 : 0) + (insuranceFileLink ? 1 : 0);
        message += `📄 *الوثائق المرفقة (${documentsCount}):*\n\n`;
        
        if (registrationFormLink) {
            message += `📝 صورة الاستمارة\n`;
        }
        
        if (insuranceFileLink) {
            message += `🛡️ ملف التأمين\n`;
        }
        
        if (!registrationFormLink && !insuranceFileLink) {
            message += `⚠️ لا توجد وثائق مرفوعة حالياً\n`;
        }
        
        message += `\n━━━━━━━━━━━━━━━━━━━━━━\n\n`;
        
        // رسالة تنبيهات وإرشادات السائق
        message += `🚗 عزيزي السائق، نتمنى لك قيادة آمنة\n\n`;
        
        message += `⚠️ *تنبيهات مهمة:*\n`;
        message += `• تأكد من تغيير زيت السيارة في موعده\n`;
        message += `• حافظ على السيارة فهي أمانة ومسؤوليتك\n`;
        message += `• تفقد مستوى الوقود والماء بانتظام\n`;
        message += `• التزم بقوانين المرور وحدود السرعة\n\n`;
        
        message += `📞 *أرقام الطوارئ المهمة:*\n`;
        message += `• نجم (المساعدة على الطريق): 920000560\n`;
        message += `• المرور: 993\n`;
        message += `• الهلال الأحمر: 997\n`;
        message += `• الشرطة: 999\n`;
        message += `• أمن الطرق: 996\n\n`;
        
        message += `━━━━━━━━━━━━━━━━━━━━━━\n`;
        message += `📅 تاريخ المشاركة: ${new Date().toLocaleDateString('ar-SA')}\n`;
        message += `🏢 نُظم - نظام إدارة المركبات`;
        
        // تحميل الوثائق كملفات
        const documentFiles = [];
        const documentUrls = [];
        
        if (registrationFormLink && registrationFormLink.trim()) {
            documentUrls.push({
                url: registrationFormLink,
                type: 'استمارة',
                filename: `${plateNumber}_استمارة`
            });
        }
        
        if (insuranceFileLink && insuranceFileLink.trim()) {
            documentUrls.push({
                url: insuranceFileLink,
                type: 'تأمين',
                filename: `${plateNumber}_تأمين`
            });
        }
        
        // تحميل الملفات
        if (documentUrls.length > 0) {
            showAlert('جاري تحميل الوثائق...', 'info');
            
            for (const doc of documentUrls) {
                try {
                    const response = await fetch(doc.url);
                    
                    if (response.ok) {
                        const blob = await response.blob();
                        
                        // تحديد الامتداد من نوع الملف
                        let extension = 'jpg';
                        if (blob.type.includes('pdf')) extension = 'pdf';
                        else if (blob.type.includes('png')) extension = 'png';
                        else if (blob.type.includes('jpeg') || blob.type.includes('jpg')) extension = 'jpg';
                        
                        const filename = `${doc.filename}.${extension}`;
                        
                        const file = new File([blob], filename, { 
                            type: blob.type || 'image/jpeg'
                        });
                        
                        documentFiles.push(file);
                    }
                } catch (err) {
                    console.log('تعذر تحميل الوثيقة:', doc.type, err);
                }
            }
        }
        
        // المشاركة مع الملفات
        if (navigator.share) {
            const shareData = {
                title: `وثائق المركبة ${plateNumber}`,
                text: message
            };
            
            // إضافة الملفات إذا كان المتصفح يدعمها
            if (documentFiles.length > 0 && navigator.canShare && navigator.canShare({ files: documentFiles })) {
                shareData.files = documentFiles;
                showAlert(`سيتم مشاركة ${documentFiles.length} وثيقة مع الرسالة ✓`, 'success');
            }
            
            await navigator.share(shareData);
            showAlert('تم مشاركة الوثائق بنجاح! ✓', 'success');
            
        } else {
            copyToClipboard(message);
        }
        
    } catch (error) {
        console.log('خطأ في المشاركة:', error);
        
        // Fallback للنسخ
        const plateNumber = document.querySelector('[data-plate-number]')?.dataset.plateNumber || '';
        const message = `🚗 وثائق المركبة ${plateNumber}\n\nتحقق من الوثائق في النظام.`;
        copyToClipboard(message);
    }
}

function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('تم نسخ تفاصيل الوثائق للحافظة!', 'success');
        }).catch(() => {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showAlert('تم نسخ تفاصيل الوثائق للحافظة!', 'success');
        } else {
            showDocumentShareModal(text);
        }
    } catch (err) {
        showDocumentShareModal(text);
    }
    
    document.body.removeChild(textArea);
}

function showDocumentShareModal(text) {
    // إنشاء نافذة منبثقة لعرض النص
    const modal = document.createElement('div');
    modal.innerHTML = `
        <div class="modal fade" id="shareDocumentsModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-success text-white">
                        <h5 class="modal-title">
                            <i class="fab fa-whatsapp me-2"></i>
                            مشاركة وثائق المركبة
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="mb-3">انسخ النص التالي وشاركه عبر الواتساب:</p>
                        <div class="form-group">
                            <textarea class="form-control" rows="15" readonly style="font-family: 'Courier New', monospace; font-size: 12px;">${text}</textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إغلاق</button>
                        <button type="button" class="btn btn-success" onclick="selectTextarea()">
                            <i class="fas fa-copy me-1"></i>تحديد الكل
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bootstrapModal = new bootstrap.Modal(document.getElementById('shareDocumentsModal'));
    bootstrapModal.show();
    
    // حذف النافذة عند إغلاقها
    document.getElementById('shareDocumentsModal').addEventListener('hidden.bs.modal', function () {
        modal.remove();
    });
}

function selectTextarea() {
    const textarea = document.querySelector('#shareDocumentsModal textarea');
    textarea.select();
    textarea.setSelectionRange(0, 99999); // للجوال
    
    try {
        document.execCommand('copy');
        showAlert('تم نسخ النص بنجاح!', 'success');
    } catch (err) {
        console.log('خطأ في النسخ');
    }
}

function showAlert(message, type) {
    // إنشاء تنبيه مؤقت
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    let icon = 'fa-check-circle';
    if (type === 'info') icon = 'fa-info-circle';
    else if (type === 'warning') icon = 'fa-exclamation-triangle';
    else if (type === 'danger') icon = 'fa-times-circle';
    
    alertDiv.innerHTML = `
        <i class="fas ${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // إزالة التنبيه بعد 4 ثوان
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 4000);
}