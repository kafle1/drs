describe('DRS Ball Tracking E2E Test Suite', () => {
  beforeEach(() => {
    // Visit the application
    cy.visit('http://localhost:3000');

    // Mock API responses for consistent testing
    cy.intercept('POST', '**/auth/login', { fixture: 'login-success.json' }).as('login');
    cy.intercept('POST', '**/videos/upload', { fixture: 'video-upload-success.json' }).as('videoUpload');
    cy.intercept('POST', '**/videos/*/track', { fixture: 'ball-tracking-success.json' }).as('ballTracking');
    cy.intercept('GET', '**/videos/*/trajectory', { fixture: 'trajectory-data.json' }).as('getTrajectory');
    cy.intercept('POST', '**/reviews', { fixture: 'review-creation-success.json' }).as('createReview');
  });

  it('Complete user journey: Upload video → Track ball → Review decision', () => {
    // Step 1: User authentication
    cy.get('[data-cy="login-button"]').click();
    cy.get('[data-cy="email-input"]').type('test@example.com');
    cy.get('[data-cy="password-input"]').type('password123');
    cy.get('[data-cy="submit-login"]').click();
    cy.wait('@login');

    // Verify user is logged in
    cy.get('[data-cy="user-menu"]').should('be.visible');

    // Step 2: Upload video
    cy.get('[data-cy="upload-video-button"]').click();

    // Create a test video file
    cy.fixture('test-video.mp4', 'binary').then((fileContent) => {
      cy.get('input[type="file"]').selectFile({
        contents: Cypress.Buffer.from(fileContent),
        fileName: 'test-match.mp4',
        mimeType: 'video/mp4'
      }, { force: true });
    });

    // Verify file is selected
    cy.get('[data-cy="selected-file-name"]').should('contain', 'test-match.mp4');

    // Click upload button
    cy.get('[data-cy="upload-submit-button"]').click();
    cy.wait('@videoUpload');

    // Verify upload success
    cy.get('[data-cy="upload-success-message"]').should('be.visible');
    cy.get('[data-cy="video-id"]').should('exist');

    // Step 3: Start ball tracking
    cy.get('[data-cy="track-ball-button"]').click();
    cy.wait('@ballTracking');

    // Verify tracking started
    cy.get('[data-cy="tracking-progress"]').should('be.visible');
    cy.get('[data-cy="tracking-status"]').should('contain', 'Processing');

    // Wait for tracking to complete (mocked)
    cy.wait('@getTrajectory');

    // Step 4: View trajectory
    cy.get('[data-cy="trajectory-viewer"]').should('be.visible');
    cy.get('[data-cy="confidence-score"]').should('be.visible');
    cy.get('[data-cy="points-count"]').should('be.visible');

    // Test 3D visualization controls
    cy.get('[data-cy="trajectory-canvas"]').should('be.visible');

    // Step 5: Create review
    cy.get('[data-cy="create-review-button"]').click();

    // Fill review form
    cy.get('[data-cy="decision-type-select"]').select('lbw');
    cy.get('[data-cy="decision-outcome-select"]').select('out');
    cy.get('[data-cy="review-notes"]').type('Clear LBW decision based on trajectory analysis');
    cy.get('[data-cy="review-confidence"]').invoke('val', '85').trigger('change');

    // Submit review
    cy.get('[data-cy="submit-review"]').click();
    cy.wait('@createReview');

    // Verify review creation
    cy.get('[data-cy="review-success-message"]').should('be.visible');

    // Step 6: Verify complete workflow
    cy.get('[data-cy="review-list"]').should('contain', 'LBW');
    cy.get('[data-cy="trajectory-summary"]').should('be.visible');
  });

  it('Error handling: Invalid file upload', () => {
    // Login first
    cy.get('[data-cy="login-button"]').click();
    cy.get('[data-cy="email-input"]').type('test@example.com');
    cy.get('[data-cy="password-input"]').type('password123');
    cy.get('[data-cy="submit-login"]').click();
    cy.wait('@login');

    // Mock upload error
    cy.intercept('POST', '**/videos/upload', {
      statusCode: 400,
      body: { detail: 'File too large. Maximum size is 100MB.' }
    }).as('uploadError');

    // Try to upload oversized file
    cy.get('[data-cy="upload-video-button"]').click();
    cy.get('input[type="file"]').selectFile('cypress/fixtures/large-video.mp4', { force: true });
    cy.get('[data-cy="upload-submit-button"]').click();

    cy.wait('@uploadError');

    // Verify error message
    cy.get('[data-cy="upload-error-message"]').should('contain', 'File too large');
  });

  it('Performance: Video processing within time limits', () => {
    // Login
    cy.get('[data-cy="login-button"]').click();
    cy.get('[data-cy="email-input"]').type('test@example.com');
    cy.get('[data-cy="password-input"]').type('password123');
    cy.get('[data-cy="submit-login"]').click();
    cy.wait('@login');

    // Upload video
    cy.get('[data-cy="upload-video-button"]').click();
    cy.get('input[type="file"]').selectFile('cypress/fixtures/test-video.mp4', { force: true });
    cy.get('[data-cy="upload-submit-button"]').click();
    cy.wait('@videoUpload');

    // Start tracking with timing
    const startTime = Date.now();
    cy.get('[data-cy="track-ball-button"]').click();
    cy.wait('@ballTracking');

    // Wait for completion
    cy.wait('@getTrajectory');
    const endTime = Date.now();
    const processingTime = endTime - startTime;

    // Verify processing time is within limits (< 60 seconds)
    expect(processingTime).to.be.lessThan(60000);
  });

  it('Accessibility: Keyboard navigation', () => {
    // Login with keyboard
    cy.get('[data-cy="login-button"]').focus().type('{enter}');
    cy.get('[data-cy="email-input"]').focus().type('test@example.com{enter}');
    cy.get('[data-cy="password-input"]').focus().type('password123{enter}');
    cy.get('[data-cy="submit-login"]').focus().type('{enter}');
    cy.wait('@login');

    // Navigate to upload with keyboard
    cy.get('[data-cy="upload-video-button"]').focus().type('{enter}');

    // Upload file with keyboard
    cy.get('input[type="file"]').selectFile('cypress/fixtures/test-video.mp4', { force: true });
    cy.get('[data-cy="upload-submit-button"]').focus().type('{enter}');
    cy.wait('@videoUpload');

    // Verify upload success is accessible
    cy.get('[data-cy="upload-success-message"]').should('be.visible');
  });

  it('Mobile responsiveness', () => {
    // Set viewport to mobile size
    cy.viewport('iphone-x');

    cy.get('[data-cy="login-button"]').should('be.visible');
    cy.get('[data-cy="login-button"]').click();

    // Verify mobile layout
    cy.get('[data-cy="mobile-menu"]').should('be.visible');

    // Login on mobile
    cy.get('[data-cy="email-input"]').type('test@example.com');
    cy.get('[data-cy="password-input"]').type('password123');
    cy.get('[data-cy="submit-login"]').click();
    cy.wait('@login');

    // Verify mobile upload interface
    cy.get('[data-cy="upload-video-button"]').should('be.visible');
    cy.get('[data-cy="upload-video-button"]').click();

    // Verify mobile file input
    cy.get('input[type="file"]').should('be.visible');
  });

  it('Data persistence: Review data survives page refresh', () => {
    // Complete review workflow
    cy.get('[data-cy="login-button"]').click();
    cy.get('[data-cy="email-input"]').type('test@example.com');
    cy.get('[data-cy="password-input"]').type('password123');
    cy.get('[data-cy="submit-login"]').click();
    cy.wait('@login');

    // Upload and track video
    cy.get('[data-cy="upload-video-button"]').click();
    cy.get('input[type="file"]').selectFile('cypress/fixtures/test-video.mp4', { force: true });
    cy.get('[data-cy="upload-submit-button"]').click();
    cy.wait('@videoUpload');

    cy.get('[data-cy="track-ball-button"]').click();
    cy.wait('@ballTracking');
    cy.wait('@getTrajectory');

    // Create review
    cy.get('[data-cy="create-review-button"]').click();
    cy.get('[data-cy="decision-type-select"]').select('run_out');
    cy.get('[data-cy="decision-outcome-select"]').select('out');
    cy.get('[data-cy="review-notes"]').type('Run out confirmed by trajectory');
    cy.get('[data-cy="submit-review"]').click();
    cy.wait('@createReview');

    // Refresh page
    cy.reload();

    // Verify review data persists
    cy.get('[data-cy="review-list"]').should('contain', 'Run Out');
    cy.get('[data-cy="trajectory-viewer"]').should('be.visible');
  });
});
