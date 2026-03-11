import cv2


class CropImage:

    def crop(self, org_img, bbox, scale, out_w, out_h, crop=True):

        if not crop:
            return cv2.resize(org_img,(out_w,out_h))

        x,y,w,h = bbox

        center_x = x + w/2
        center_y = y + h/2

        new_w = w*scale
        new_h = h*scale

        x1 = int(center_x - new_w/2)
        y1 = int(center_y - new_h/2)
        x2 = int(center_x + new_w/2)
        y2 = int(center_y + new_h/2)

        h_img,w_img = org_img.shape[:2]

        x1 = max(0,x1)
        y1 = max(0,y1)
        x2 = min(w_img,x2)
        y2 = min(h_img,y2)

        cropped = org_img[y1:y2, x1:x2]

        return cv2.resize(cropped,(out_w,out_h))