import cv2
import numpy as np
import matplotlib.pyplot as plt

def get_keypoints_and_descriptors(imgL, imgR):
    """Use ORB detector and FLANN matcher to get keypoints, descritpors,
    and corresponding matches that will be good for computing
    homography.
    """
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(imgL, None)
    kp2, des2 = orb.detectAndCompute(imgR, None)

    ############## Using FLANN matcher ##############
    # Each keypoint of the first image is matched with a number of
    # keypoints from the second image. k=2 means keep the 2 best matches
    # for each keypoint (best matches = the ones with the smallest
    # distance measurement).
    FLANN_INDEX_LSH = 6
    index_params = dict(
        algorithm=FLANN_INDEX_LSH,
        table_number=6,  # 12
        key_size=12,  # 20
        multi_probe_level=1,
    )  # 2
    search_params = dict(checks=50)  # or pass empty dictionary
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    flann_match_pairs = flann.knnMatch(des1, des2, k=2)
    return kp1, des1, kp2, des2, flann_match_pairs


def lowes_ratio_test(matches, ratio_threshold=0.6):
    """Filter matches using the Lowe's ratio test.

    The ratio test checks if matches are ambiguous and should be
    removed by checking that the two distances are sufficiently
    different. If they are not, then the match at that keypoint is
    ignored.

    https://stackoverflow.com/questions/51197091/how-does-the-lowes-ratio-test-work
    """
    filtered_matches = []
    for m, n in matches:
        if m.distance < ratio_threshold * n.distance:
            filtered_matches.append(m)
    return filtered_matches

def draw_matches(im1, im2, pts1, pts2):
    # Draw the matches between the images
    img_matches = cv2.drawMatches(im1, [cv2.KeyPoint(float(pt[0]), float(pt[1]), 1) for pt in pts1], 
                                im2, [cv2.KeyPoint(float(pt[0]), float(pt[1]), 1) for pt in pts2], 
                                [cv2.DMatch(i, i, 0) for i in range(len(pts1))], None)

    # Display the matches
    plt.figure(figsize=(10, 5))
    plt.imshow(img_matches)

    # Annotate the points with their index numbers
    for i, (pt1, pt2) in enumerate(zip(pts1, pts2)):
        plt.text(pt1[0], pt1[1], str(i), color='red', fontsize=12)
        plt.text(pt2[0] + im1.shape[1], pt2[1], str(i), color='red', fontsize=12)

    plt.show()

def compute_fundamental_matrix(matches, kp1, kp2, method=cv2.FM_RANSAC, reproj=3, confidence=0.99):
    """Use the set of good mathces to estimate the Fundamental Matrix.

    See  https://en.wikipedia.org/wiki/Eight-point_algorithm#The_normalized_eight-point_algorithm
    for more info.
    """
    pts1, pts2 = [], []
    fundamental_matrix, inliers = None, None
    for m in matches[:8]:
        pts1.append(kp1[m.queryIdx].pt)
        pts2.append(kp2[m.trainIdx].pt)
    if pts1 and pts2:
        # You can play with the Threshold and confidence values here
        # until you get something that gives you reasonable results. I
        # used the defaults
        fundamental_matrix, inliers = cv2.findFundamentalMat(
            np.float32(pts1),
            np.float32(pts2),
            method=method,
            ransacReprojThreshold=reproj,
            confidence=confidence,
        )
    return fundamental_matrix, inliers, pts1, pts2

def select_features(img):
    coordinates = []
    def get_pixel_coordinates(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:  # Check if the left mouse button was clicked
            coordinates.append((x, y))

    # Display the image in a window
    cv2.namedWindow('Image', cv2.WINDOW_NORMAL)
    cv2.imshow('Image', img)
    height, width = img.shape[:2]
    # Resize the window to fit the whole image but be in a smaller panel
    cv2.resizeWindow('Image', width // 4, height // 4)

    # Set the mouse callback function to get_pixel_coordinates
    cv2.setMouseCallback('Image', get_pixel_coordinates)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return coordinates